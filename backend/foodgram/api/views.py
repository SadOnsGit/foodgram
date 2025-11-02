from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .filters import ReceiptFilter
from .pagination import UserPageNumberPagination
from .serializers import (
    ChangePasswordSerializer,
    CreateReceiptSerializer,
    GetUserSerializer,
    ReceiptSerializer,
    TagSerializer,
    CreateUserSerializer,
    DetailUserSerializer,
    UpdateAvatarSerializer,
)
from food.models import Receipts, Tags
from users.models import Follow

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
                )
            )
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        if self.action in ['retrieve', 'list', 'me']:
            return DetailUserSerializer
        if self.action == 'avatar_actions':
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


class TagsListView(APIView):

    def get(self, request):
        tags = Tags.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class TagsRetrieveView(APIView):

    def get(self, request, pk):
        tag = get_object_or_404(Tags, pk=pk)
        serializer = TagSerializer(tag)
        return Response(serializer.data)


class ReceiptViewSet(ModelViewSet):
    queryset = Receipts.objects.all().prefetch_related(
        "favorited_receipts", "purchased_receipts"
    )
    serializer_class = ReceiptSerializer
    permission_classes = (IsAuthenticated,)
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
