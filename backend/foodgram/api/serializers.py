from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from .constants import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
)
from .fields import Base64ImageField
from food.models import FavoriteReceipts, Ingredients, Receipts, Tags, IngredientInReceipt

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
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

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )
        return user

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


class GetUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "avatar")


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
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInReceipt
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ReceiptSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True)

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.purchases_by.filter(buyer=user).exists()
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
        return ReceiptSerializer(
            instance,
            context=self.context
        ).data

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Укажите хотя бы один ингредиент')
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        receipt = Receipts.objects.create(**validated_data)
        receipt.tags.set(tags_data)
        ingredient_objects = []
        for item in ingredients_data:
            ingredient_objects.append(
                IngredientInReceipt(
                    receipt=receipt,
                    ingredient_id=item['id'],
                    amount=item['amount']
                )
            )
        IngredientInReceipt.objects.bulk_create(ingredient_objects)

        return receipt

    class Meta:
        model = Receipts
        fields = (
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )
