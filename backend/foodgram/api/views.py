from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model


from .serializers import NewUserSerializer
from .pagination import UserPageNumberPagination


User = get_user_model()


class NewUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = NewUserSerializer
    permission_classes = (AllowAny,)
    pagination_class = UserPageNumberPagination

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("Удаление объектов не разрешено.")