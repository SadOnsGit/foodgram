from rest_framework import serializers
from django.contrib.auth import get_user_model

from .constants import MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_EMAIL_LENGTH,
    )
    first_name = serializers.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
    )
    last_name = serializers.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
    )
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class GetUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name')