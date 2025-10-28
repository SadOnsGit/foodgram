from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import NewUserViewSet, SetPassword

v1_router = DefaultRouter()
v1_router.register("users", NewUserViewSet)

urlpatterns = [
    path(
        "auth/token/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        'users/set_password/',
        SetPassword.as_view(),
        name='set_password'
    ),
    path("", include(v1_router.urls)),
]
