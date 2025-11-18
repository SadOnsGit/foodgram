import os
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework import status

from users.models import Follow
from food.constants import SHORT_CODE_URLS_MAX_LENGTH
from food.models import FavoriteRecipe, Ingredients, Recipe, ShoppingListRecipe, Tags
from .filters import IngredientFilter, RecipeFilter
from .pagination import UserPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (ChangePasswordSerializer, CreateRecipeSerializer,
                          DetailUserSerializer,
                          FollowUserSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShortSerializer, TagSerializer,
                          UpdateAvatarSerializer)
from .utils import generate_shopping_cart_pdf

User = get_user_model()


def redirect_to_recipe(request, recipe_short_code):
    try:
        recipe = Recipe.objects.get(short_code=recipe_short_code)
        return redirect('recipe_detail', recipe.id)
    except Recipe.DoesNotExist:
        return redirect('/not-found/')


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = DetailUserSerializer
    pagination_class = UserPageNumberPagination
    http_method_names = ["get", "post", "put", "delete"]

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.annotate(
            recipes_count=Count("recipe", distinct=True),
        ).prefetch_related("recipe")
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed=Exists(
                    Follow.objects.filter(user=user, following=OuterRef("pk"))
                )
            )
        else:
            queryset = queryset.annotate(
                is_subscribed=Value(False, output_field=BooleanField())
            )
        return queryset

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        url_name="me",
        permission_classes=[IsAuthenticated],
        serializer_class=DetailUserSerializer,
    )
    def me(self, request, *args, **kwargs):
        user = self.get_queryset().get(pk=request.user.pk)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        url_name="avatar_actions",
        permission_classes=[IsAuthenticated],
        serializer_class=UpdateAvatarSerializer,
    )
    def avatar_actions(self, request, *args, **kwargs):
        if request.method == "PUT":
            serializer = self.get_serializer(
                request.user, data=request.data, partial=False
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="subscribe",
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        following = get_object_or_404(self.get_queryset(), pk=pk)
        user = request.user

        if request.method == "POST":
            if user == following:
                return Response(
                    {"detail": "Нельзя подписаться на самого себя!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow, created = Follow.objects.get_or_create(
                user=user,
                following=following
            )
            if not created:
                return Response(
                    {"detail": "Вы уже подписаны!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = FollowUserSerializer(
                following,
                context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if Follow.objects.filter(user=user, following=following).exists():
            Follow.objects.filter(user=user, following=following).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=[IsAuthenticated],
        pagination_class=UserPageNumberPagination,
        filter_backends=(DjangoFilterBackend,),
    )
    def subscriptions(self, request):
        queryset = self.get_queryset().filter(followers__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FollowUserSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowUserSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class TagsReadOnlyViewSet(ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        "recipe_add_favorite_by", "cart_add_by"
    )
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,)
    pagination_class = UserPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH"]:
            return CreateRecipeSerializer
        return RecipeSerializer

    @action(
        methods=("get",),
        detail=True,
        permission_classes=(AllowAny,),
        url_path="get-link",
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        relative_url = reverse("redirect_to_recipe", args=[recipe.short_code])
        full_url = request.build_absolute_uri(relative_url)

        return Response({"short-link": full_url}, status=status.HTTP_200_OK)

    @action(
        methods=("post", "delete"),
        detail=True,
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite_recipe(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if request.method == 'POST':
            _, created = FavoriteRecipe.objects.get_or_create(
                recipe=recipe,
                user=user
            )
            if created:
                serializer = RecipeShortSerializer(recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"message": "Рецепт уже находится в избранном"},
                status=status.HTTP_400_BAD_REQUEST
            )
        deleted_count, _ = FavoriteRecipe.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Рецепт не находится в избранном."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=("post", "delete"),
        detail=True,
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if request.method == 'POST':
            _, created = ShoppingListRecipe.objects.get_or_create(
                recipe=recipe,
                user=user
            )
            if created:
                serializer = RecipeShortSerializer(recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"message": "Рецепт уже находится в корзине"},
                status=status.HTTP_400_BAD_REQUEST
            )
        deleted_count, _ = ShoppingListRecipe.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Рецепт не находится в корзине."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=("get",),
        detail=False,
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        buffer = generate_shopping_cart_pdf(self.request.user)
        response = HttpResponse(buffer, content_type="application/pdf")
        content_disposition = 'attachment; filename="shopping_cart.pdf"'
        response["Content-Disposition"] = content_disposition
        return response


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer


class LogoutView(APIView):
    def post(self, request):
        return Response({"detail": "Выход выполнен успешно."}, status=204)
