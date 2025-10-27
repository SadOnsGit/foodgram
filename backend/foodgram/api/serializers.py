from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from .fields import Base64ImageField

from .constants import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
)

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
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )
        return user


    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password', 'is_subscribed', 'avatar')


class GetUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'avatar')


class NewTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        access_token = AccessToken.for_user(user)
        return {'auth_token': str(access_token)}
