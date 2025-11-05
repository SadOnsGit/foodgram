from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Exists, OuterRef, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.http import HttpResponse
import os

from .filters import ReceiptFilter
from .pagination import UserPageNumberPagination
from .serializers import (
    ChangePasswordSerializer,
    CreateReceiptSerializer,
    CreateUserSerializer,
    DetailUserSerializer,
    IngredientSerializer,
    ReceiptSerializer,
    TagSerializer,
    UpdateAvatarSerializer,
    FollowUserSerializer,
)
from food.models import Ingredients, Receipts, Tags
from users.models import Follow
from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class NewUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = UserPageNumberPagination
    http_method_names = ["get", "post", "put", "delete"]

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=405)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return User.objects.annotate(
                is_subscribed=Exists(
                    Follow.objects.filter(user=user, following=OuterRef("pk"))
                ),
                recipes_count=Count('receipts', distinct=True)
            ).prefetch_related('receipts')
        return User.objects.all()

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
                request.user, data=request.data, partial=True
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

        if request.method == 'POST':
            if user == following:
                return Response(
                    {"detail": "Нельзя подписаться на самого себя!"},
                    status=400
                )
            if Follow.objects.filter(user=user, following=following).exists():
                return Response({"detail": "Вы уже подписаны!"}, status=400)

            Follow.objects.create(user=user, following=following)
            serializer = FollowUserSerializer(following, context={'request': request})
            return Response(serializer.data, status=201)

        elif request.method == 'DELETE':
            get_object_or_404(Follow, user=user, following=following).delete()
            return Response(status=204)


    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        follows = request.user.following.all()
        serializer = FollowUserSerializer(follows, context={'request': request}, many=True)
        return Response(serializer.data, status=200)


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
                    {"current_password": ["Wrong password."]}, status=400
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


class ReceiptViewSet(ModelViewSet):
    queryset = Receipts.objects.all().prefetch_related(
        "favorited_receipts", "purchased_receipts"
    )
    serializer_class = ReceiptSerializer
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
    pagination_class = UserPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ReceiptFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH"]:
            return CreateReceiptSerializer
        return ReceiptSerializer


class FavoriteReceiptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        receipt = get_object_or_404(Receipts, pk=pk)
        user = self.request.user
        if not user.favorite_receipts.filter(pk=receipt.pk).exists():
            user.favorite_receipts.add(receipt)
            return Response(
                {
                    "id": receipt.pk,
                    "name": receipt.name,
                    "image": request.build_absolute_uri(receipt.image.url),
                    "cooking_time": receipt.cooking_time,
                },
                status=201,
            )
        return Response(
            {"message": "Рецепт уже находится в избранном"}, status=400
        )

    def delete(self, request, pk):
        receipt = get_object_or_404(Receipts, pk=pk)
        user = self.request.user
        if user.favorite_receipts.filter(pk=receipt.pk).exists():
            user.favorite_receipts.remove(receipt)
            return Response(
                {"message": "Рецепт удален из избранного"}, status=204
            )
        return Response(
            {"message": "Рецепт не находится в избранном"}, status=400
        )


class PurchasedReceiptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        receipt = get_object_or_404(Receipts, pk=pk)
        user = self.request.user
        if not user.purchases.filter(pk=receipt.pk).exists():
            user.purchases.add(receipt)
            return Response(
                {
                    "id": receipt.pk,
                    "name": receipt.name,
                    "image": request.build_absolute_uri(receipt.image.url),
                    "cooking_time": receipt.cooking_time,
                },
                status=201,
            )
        return Response(
            {"message": "Рецепт уже находится в списке покупок"}, status=400
        )

    def delete(self, request, pk):
        receipt = get_object_or_404(Receipts, pk=pk)
        user = self.request.user
        if user.purchases.filter(pk=receipt.pk).exists():
            user.purchases.remove(receipt)
            return Response(
                {"message": "Рецепт удален из списка покупок"}, status=204
            )
        return Response(
            {"message": "Рецепт не находится в списке покупок"}, status=400
        )


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer



class DownloadShoppingCartUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        font_path = os.path.join('fonts', 'DejaVuSans.ttf')
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))
        p.setFont('DejaVu', 12)

        all_obj_shopping_cart = self.request.user.purchases.all()
        p.drawString(100, height - 100, "Список покупок рецептов")
        y_position = height - 130

        for receipt in all_obj_shopping_cart:
            p.drawString(100, y_position, f"Номер: {receipt.id}")
            y_position -= 20
            p.drawString(100, y_position, f"Название: {receipt.name}")
            y_position -= 20
            p.drawString(100, y_position, f"Описание: {receipt.text}")
            y_position -= 20
            p.drawString(100, y_position, f"Время готовки: {receipt.cooking_time} minutes")
            y_position -= 20
            p.drawString(100, y_position, f"Изображение: ")
            y_position -= 20
            if receipt.image:
                image_path = receipt.image.path
                p.drawImage(image_path, 100, y_position - 100, width=200, height=100)
                y_position -= 120
            else:
                y_position -= 60

        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'
        return response
