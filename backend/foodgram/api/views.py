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
    GetUserSerializer,
    ReceiptSerializer,
    TagSerializer,
    UserSerializer,
)
from food.models import FavoriteReceipts, Ingredients, Receipts, Tags
from users.models import Follow

User = get_user_model()


class NewUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
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

    @action(
        detail=False,
        methods=["get", "put", "delete"],
        url_path="me",
        url_name="me",
        permission_classes=[IsAuthenticated],
        serializer_class=GetUserSerializer,
    )
    def me(self, request, *args, **kwargs):
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
        "favorited_by", "purchases_by"
    )
    serializer_class = ReceiptSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = UserPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ReceiptFilter
