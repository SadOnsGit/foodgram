from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from users.models import Follow
from .constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
                        MAX_LAST_NAME_LENGTH)
from food.models import IngredientInRecipe, Ingredients, Recipe, Tags
from .fields import Base64ImageField

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_EMAIL_LENGTH,
    )
    first_name = serializers.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
    )
    last_name = serializers.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
    )
    password = serializers.CharField(
        write_only=True,
    )

    def create(self, validated_data):
        email = validated_data["email"]
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "Данный e-mail уже зарегистрирован!"}
            )
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class DetailUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_EMAIL_LENGTH,
    )
    first_name = serializers.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
    )
    last_name = serializers.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
    )
    password = serializers.CharField(
        write_only=True,
    )
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return Follow.objects.filter(user=request.user, following=obj).exists()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
            "avatar",
        )


class UpdateAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ("avatar",)


class NewTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
        access_token = AccessToken.for_user(user)
        return {"auth_token": str(access_token)}


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    author = DetailUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True)

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorite_recipe.filter(pk=obj.pk).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.purchases.filter(pk=obj.pk).exists()
        return False

    def get_ingredients(self, obj):
        queryset = obj.recipe_ingredients.all()
        return IngredientInRecipeSerializer(queryset, many=True).data

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def validate_id(self, value):
        if not Ingredients.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиент не существует")
        return value


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username",
        read_only=True
    )
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True
    )
    ingredients = IngredientAmountSerializer(many=True)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        ingredients = data.get("ingredients", [])
        tags = data.get("tags", [])
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Укажите хотя бы один ингредиент."}
            )
        if not tags:
            raise serializers.ValidationError(
                {"tags": "Укажите хотя бы один тег."}
            )

        ingredient_ids = set()
        for i, item in enumerate(ingredients):
            ing_id = item.get("id")
            amount = item.get("amount")
            if not amount or amount <= 0:
                raise serializers.ValidationError(
                    {
                        "ingredients": f"Кол-во у id={ing_id} должно быть > 0."
                    }
                )
            if ing_id in ingredient_ids:
                raise serializers.ValidationError(
                    {"ingredients": f"Ингредиент с id={ing_id} уже добавлен."}
                )
            ingredient_ids.add(ing_id)

        tag_ids = set()
        for i, tag in enumerate(tags):
            tag_id = tag.id
            if tag_id in tag_ids:
                raise serializers.ValidationError(
                    {"tags": f"Тег с id={tag_id} уже добавлен."}
                )
            tag_ids.add(tag_id)

        cooking_time = data.get("cooking_time")
        if not cooking_time or cooking_time <= 0:
            raise serializers.ValidationError(
                {"cooking_time": "Время приготовления должно быть больше 0."}
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        ingredient_objects = []
        for item in ingredients_data:
            ingredient_objects.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient_id=item["id"],
                    amount=item["amount"],
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_objects)

        return recipe

    class Meta:
        model = Recipe
        fields = (
            "author",
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = "__all__"


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowUserSerializer(serializers.ModelSerializer):
    recipes_count = serializers.IntegerField(read_only=True)
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        limit = None
        if recipes_limit is not None:
            try:
                limit = int(recipes_limit)
                if limit < 0:
                    limit = None
            except ValueError:
                limit = None

        queryset = obj.recipe.all()
        if limit:
            queryset = queryset[:limit]

        return RecipeShortSerializer(queryset, many=True, read_only=True).data

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, following=obj).exists()
