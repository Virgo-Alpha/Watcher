"""
URL configuration for watcher project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoints
    path('', include('apps.common.urls')),
    
    # API endpoints
    path('api/v1/', include('apps.authentication.urls')),
    path('api/v1/', include('apps.haunts.urls')),
    path('api/v1/', include('apps.subscriptions.urls')),
    path('api/v1/', include('apps.rss.api_urls')),
    path('api/v1/', include('apps.scraping.urls')),
    path('api/v1/', include('apps.ai.urls')),
    path('rss/', include('apps.rss.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]