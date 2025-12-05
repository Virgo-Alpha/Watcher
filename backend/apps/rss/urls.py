"""
RSS feed URL configuration for XML feeds.
"""
from django.urls import path
from apps.rss import views

app_name = 'rss'

urlpatterns = [
    # Private RSS feed (requires authentication)
    path('private/<uuid:haunt_id>/', views.private_rss_feed, name='private-feed'),

    # Public RSS feed (no authentication required)
    path('public/<slug:public_slug>/', views.public_rss_feed, name='public-feed'),

    # Get RSS URL for a haunt
    path('url/<uuid:haunt_id>/', views.get_rss_url, name='get-url'),
]