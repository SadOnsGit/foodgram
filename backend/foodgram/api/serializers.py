from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from .constants import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
)
from .fields import Base64ImageField
from food.models import IngredientInReceipt, Ingredients, Receipts, Tags
from users.models import Follow

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
    is_subscribed = serializers.BooleanField(read_only=True)

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
    avatar = Base64ImageField(required=True, allow_null=True)

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


class IngredientInReceiptSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInReceipt
        fields = ("id", "name", "measurement_unit", "amount")


class ReceiptSerializer(serializers.ModelSerializer):
    author = DetailUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True)

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorite_receipts.filter(pk=obj.pk).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.purchases.filter(pk=obj.pk).exists()
        return False

    def get_ingredients(self, obj):
        queryset = obj.receipt_ingredients.all()
        return IngredientInReceiptSerializer(queryset, many=True).data

    class Meta:
        model = Receipts
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


class CreateReceiptSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True
    )
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True
    )
    ingredients = IngredientAmountSerializer(many=True)

    def to_representation(self, instance):
        return ReceiptSerializer(instance, context=self.context).data

    def validate(self, data):
        ingredients = data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError(
                "Укажите хотя бы один ингредиент"
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        receipt = Receipts.objects.create(**validated_data)
        receipt.tags.set(tags_data)
        ingredient_objects = []
        for item in ingredients_data:
            ingredient_objects.append(
                IngredientInReceipt(
                    receipt=receipt,
                    ingredient_id=item["id"],
                    amount=item["amount"],
                )
            )
        IngredientInReceipt.objects.bulk_create(ingredient_objects)

        return receipt

    class Meta:
        model = Receipts
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
        model = Receipts
        fields = ("id", "name", "image", "cooking_time")


class FollowUserSerializer(serializers.ModelSerializer):
    recipes_count = serializers.IntegerField(read_only=True)
    receipts = RecipeShortSerializer(many=True, read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "receipts",
            "recipes_count",
            "avatar",
        )
