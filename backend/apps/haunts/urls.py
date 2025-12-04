from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, UserUIPreferencesViewSet, HauntViewSet, PublicHauntViewSet

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'preferences', UserUIPreferencesViewSet, basename='preferences')
router.register(r'haunts', HauntViewSet, basename='haunt')
router.register(r'public/haunts', PublicHauntViewSet, basename='public-haunt')

urlpatterns = [
    path('', include(router.urls)),
]