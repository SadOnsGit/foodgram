from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (DownloadShoppingCartUser, FavoriteRecipeView,
                    IngredientsViewSet, LogoutView, NewUserViewSet,
                    PurchasedRecipeView, RecipeViewSet, SetPassword,
                    TagsReadOnlyViewSet)

v1_router = DefaultRouter()
v1_router.register("users", NewUserViewSet)
v1_router.register("recipes", RecipeViewSet)
v1_router.register("tags", TagsReadOnlyViewSet)
v1_router.register("ingredients", IngredientsViewSet)

urlpatterns = [
    path(
        "auth/token/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/logout/",
        LogoutView.as_view(),
    ),
    path("users/set_password/", SetPassword.as_view(), name="set_password"),
    path("recipes/<int:pk>/favorite/", FavoriteRecipeView.as_view()),
    path("recipes/<int:pk>/shopping_cart/", PurchasedRecipeView.as_view()),
    path(
        "recipes/download_shopping_cart/",
        DownloadShoppingCartUser.as_view()
    ),
    path("", include(v1_router.urls)),
]
