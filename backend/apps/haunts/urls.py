"""
URL configuration for haunts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, UserUIPreferencesViewSet, HauntViewSet, PublicHauntViewSet

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'preferences', UserUIPreferencesViewSet, basename='preferences')
router.register(r'haunts', HauntViewSet, basename='haunt')
router.register(r'public/haunts', PublicHauntViewSet, basename='public-haunt')

urlpatterns = [
    # Explicit URL patterns for custom actions (must come before router.urls)
    path('haunts/generate-config-preview/', 
         HauntViewSet.as_view({'post': 'generate_config_preview'}), 
         name='haunt-generate-config-preview'),
    path('haunts/test-scrape/', 
         HauntViewSet.as_view({'post': 'test_scrape'}), 
         name='haunt-test-scrape'),
    path('', include(router.urls)),
]
