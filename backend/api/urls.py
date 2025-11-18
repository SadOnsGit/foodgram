from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (IngredientsViewSet,
                    RecipeViewSet, UserViewSet,
                    TagsReadOnlyViewSet, LogoutView)

router = DefaultRouter()
router.register("users", UserViewSet)
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
    path("", include(router.urls)),
]
