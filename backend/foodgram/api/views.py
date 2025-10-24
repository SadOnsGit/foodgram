from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .pagination import UserPageNumberPagination
from .serializers import RegisterUserSerializer

User = get_user_model()


class NewUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = (AllowAny,)
    pagination_class = UserPageNumberPagination
    http_method_names = ["get", "post"]

    @action(
        detail=False,
        methods=["get", "patch"],
        url_path="me",
        url_name="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        # if request.method == "PATCH":
        #     serializer = self.get_serializer(
        #         request.user, data=request.data, partial=True
        #     )
        #     serializer.is_valid(raise_exception=True)
        #     return Response(serializer.data)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
