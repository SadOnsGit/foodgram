from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from users.models import Follow
from users.constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
                             MAX_LAST_NAME_LENGTH)
from food.models import IngredientInRecipe, Ingredients, Recipe, Tags
from .fields import Base64ImageField

User = get_user_model()


class DetailUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and obj
            and Follow.objects.filter(
                user=request.user, following=obj
            ).exists()
        )

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )


class FollowUserSerializer(DetailUserSerializer):
    recipes_count = serializers.IntegerField(read_only=True)
    recipes = serializers.SerializerMethodField()

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
    id = serializers.PrimaryKeyRelatedField(source="ingredient", read_only=True)
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
    ingredients = IngredientInRecipeSerializer(source='recipe_ingredients')
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True)

    def get_is_favorited(self, obj):
        request = self.context["request"]
        if request and request.user.is_authenticated and obj:
            return request.user.favorite_recipe.filter(pk=obj.pk).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context["request"]
        if request and request.user.is_authenticated and obj:
            return request.user.purchases.filter(pk=obj.pk).exists()
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
    ingredients = IngredientInRecipeSerializer(source='recipe_ingredients')

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
            if ing_id in ingredient_ids:
                raise serializers.ValidationError(
                    {"ingredients": f"Ингредиент с id={ing_id} уже добавлен."}
                )
            ingredient_ids.add(ing_id)

        if len(tags) > set(tags):
            raise serializers.ValidationError(
                {"tags": f"Тег уже добавлен."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        request = self.context.get("request")
        recipe = Recipe.objects.create(**validated_data, author=request.user)
        recipe.tags.set(tags_data)
        ingredient_objects = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=item["id"],
                amount=item["amount"],
            )
            for item in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_objects)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tags_data is not None:
            instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()

        ingredient_objects = [
            IngredientInRecipe(
                recipe=instance,
                ingredient_id=item["id"],
                amount=item["amount"],
            )
            for item in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_objects)

        instance.save()
        return instance

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
