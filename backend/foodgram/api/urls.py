from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NewUserViewSet

v1_router = DefaultRouter()
v1_router.register('users', NewUserViewSet)

urlpatterns = [
    path('', include('djoser.urls.jwt')),
    path('', include(v1_router.urls)),
]
