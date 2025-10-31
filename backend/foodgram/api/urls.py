from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    FavoriteReceiptView,
    NewUserViewSet,
    PurchasedReceiptView,
    ReceiptViewSet,
    SetPassword,
    TagsListView,
    TagsRetrieveView,
)

v1_router = DefaultRouter()
v1_router.register("users", NewUserViewSet)
v1_router.register("recipes", ReceiptViewSet)

urlpatterns = [
    path(
        "auth/token/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("users/set_password/", SetPassword.as_view(), name="set_password"),
    path("tags/", TagsListView.as_view(), name="tags_list"),
    path("tags/<int:pk>/", TagsRetrieveView.as_view(), name="tags_obj"),
    path("recipes/<int:pk>/favorite/", FavoriteReceiptView.as_view()),
    path("recipes/<int:pk>/shopping_cart/", PurchasedReceiptView.as_view()),
    path("", include(v1_router.urls)),
]
