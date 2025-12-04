"""
URL configuration for subscription management API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, UserReadStateViewSet

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'read-states', UserReadStateViewSet, basename='readstate')

urlpatterns = [
    path('', include(router.urls)),
]