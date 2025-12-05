"""
RSS API URL configuration for REST endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.rss import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'rss/items', views.RSSItemViewSet, basename='rssitem')

urlpatterns = [
    path('', include(router.urls)),
]
