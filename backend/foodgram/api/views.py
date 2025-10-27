from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Exists, OuterRef

from .pagination import UserPageNumberPagination
from .serializers import UserSerializer, GetUserSerializer
from users.models import Follow

User = get_user_model()


class NewUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    pagination_class = UserPageNumberPagination
    http_method_names = ["get", "post", "put", "delete"]


    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method Not Allowed"},
            status=405
        )
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return User.objects.annotate(
                is_subscribed=Exists(
                    Follow.objects.filter(user=user, following=OuterRef('pk'))
                )
            )
        return User.objects.all()
    @action(
        detail=False,
        methods=["get", "put", "delete"],
        url_path="me",
        url_name="me",
        permission_classes=[IsAuthenticated],
        serializer_class=GetUserSerializer
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