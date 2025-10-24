from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class NewUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=250,
    )
    first_name = serializers.CharField(
        max_length=150,
    )
    last_name = serializers.CharField(
        max_length=150,
    )
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')