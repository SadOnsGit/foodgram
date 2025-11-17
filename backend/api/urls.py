from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (DownloadShoppingCartUser, FavoriteRecipeView,
                    IngredientsViewSet, LogoutView, NewUserViewSet,
                    PurchasedRecipeView, RecipeViewSet, SetPassword,
                    TagsReadOnlyViewSet)

router = DefaultRouter()
router.register("users", NewUserViewSet)
router.register("recipes", RecipeViewSet)
router.register("tags", TagsReadOnlyViewSet)
router.register("ingredients", IngredientsViewSet)

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
    path("", include(router.urls)),
]
