import os
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.models import Follow
from food.constants import SHORT_CODE_URLS_MAX_LENGTH
from food.models import Ingredients, Recipe, Tags
from .filters import IngredientFilter, RecipeFilter
from .pagination import UserPageNumberPagination
from .permissions import IsAuthorOrReadOnly, IsUserOrReadOnly
from .serializers import (ChangePasswordSerializer, CreateRecipeSerializer,
                          CreateUserSerializer, DetailUserSerializer,
                          FollowUserSerializer, IngredientSerializer,
                          RecipeSerializer, TagSerializer,
                          UpdateAvatarSerializer)
from .utils import generate_unique_short_code

User = get_user_model()


def redirect_to_recipe(request, recipe_short_code):
    recipe = get_object_or_404(Recipe, short_code=recipe_short_code)
    return HttpResponseRedirect(
        request.build_absolute_uri(f"/recipe/{recipe.id}/")
    )


class NewUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = UserPageNumberPagination
    http_method_names = ["get", "post", "put", "delete"]

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=405)

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

    def get_permissions(self):
        if self.action in ["update"]:
            self.permission_classes = [IsUserOrReadOnly]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        if self.action in ["retrieve", "list", "me"]:
            return DetailUserSerializer
        if self.action == "avatar_actions":
            return UpdateAvatarSerializer
        return DetailUserSerializer

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

        elif request.method == "DELETE":
            request.user.avatar = None
            request.user.save()
            return Response(status=204)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

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
                    status=400,
                )
            if Follow.objects.filter(user=user, following=following).exists():
                return Response({"detail": "Вы уже подписаны!"}, status=400)

            Follow.objects.create(user=user, following=following)
            serializer = FollowUserSerializer(
                following,
                context={"request": request}
            )
            return Response(serializer.data, status=201)

        elif request.method == "DELETE":
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(status=204)
            return Response(status=400)

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


class SetPassword(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(
                serializer.validated_data["current_password"]
            ):
                return Response(
                    {"current_password": ["Wrong password."]},
                    status=400
                )
            user.password = make_password(
                serializer.validated_data["new_password"]
            )
            user.save()
            return Response(status=204)

        return Response(serializer.errors, status=400)


class TagsReadOnlyViewSet(ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        "in_favorites", "in_shopping_list"
    )
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = UserPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        code = generate_unique_short_code(SHORT_CODE_URLS_MAX_LENGTH)
        serializer.save(author=self.request.user, short_code=code)

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

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

        return Response({"short-link": full_url}, status=200)


class FavoriteRecipeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if not user.favorite_recipe.filter(pk=recipe.pk).exists():
            user.favorite_recipe.add(recipe)
            return Response(
                {
                    "id": recipe.pk,
                    "name": recipe.name,
                    "image": request.build_absolute_uri(recipe.image.url),
                    "cooking_time": recipe.cooking_time,
                },
                status=201,
            )
        return Response(
            {"message": "Рецепт уже находится в избранном"},
            status=400
        )

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if user.favorite_recipe.filter(pk=recipe.pk).exists():
            user.favorite_recipe.remove(recipe)
            return Response(
                {"message": "Рецепт удален из избранного"},
                status=204
            )
        return Response(
            {"message": "Рецепт не находится в избранном"},
            status=400
        )


class PurchasedRecipeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if not user.purchases.filter(pk=recipe.pk).exists():
            user.purchases.add(recipe)
            return Response(
                {
                    "id": recipe.pk,
                    "name": recipe.name,
                    "image": request.build_absolute_uri(recipe.image.url),
                    "cooking_time": recipe.cooking_time,
                },
                status=201,
            )
        return Response(
            {"message": "Рецепт уже находится в списке покупок"}, status=400
        )

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if user.purchases.filter(pk=recipe.pk).exists():
            user.purchases.remove(recipe)
            return Response(
                {"message": "Рецепт удален из списка покупок"},
                status=204
            )
        return Response(
            {"message": "Рецепт не находится в списке покупок"},
            status=400
        )


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer


class DownloadShoppingCartUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        font_path = os.path.join("fonts", "DejaVuSans.ttf")
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))
        p.setFont("DejaVu", 12)

        all_obj_shopping_cart = self.request.user.purchases.all()
        p.drawString(100, height - 100, "Список покупок рецептов")
        y_position = height - 130

        for recipe in all_obj_shopping_cart:
            p.drawString(100, y_position, f"Номер: {recipe.id}")
            y_position -= 20
            p.drawString(100, y_position, f"Название: {recipe.name}")
            y_position -= 20
            p.drawString(100, y_position, f"Описание: {recipe.text}")
            y_position -= 20
            p.drawString(
                100,
                y_position,
                f"Время готовки: {recipe.cooking_time} minutes",
            )
            y_position -= 20
            p.drawString(100, y_position, "Изображение: ")
            y_position -= 20
            if recipe.image:
                image_path = recipe.image.path
                p.drawImage(
                    image_path,
                    100,
                    y_position - 100,
                    width=200,
                    height=100
                )
                y_position -= 120
            else:
                y_position -= 60

        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        content_disposition = 'attachment; filename="shopping_cart.pdf"'
        response["Content-Disposition"] = content_disposition
        return response


class LogoutView(APIView):

    def post(self, request):
        return Response({"detail": "Выход выполнен успешно."}, status=204)
