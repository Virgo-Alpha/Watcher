"""
RSS feed views for serving RSS XML feeds.
"""
import logging
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.haunts.models import Haunt
from apps.rss.services import RSSService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def private_rss_feed(request, haunt_id):
    """
    Serve private RSS feed for authenticated user's haunt.

    Args:
        request: HTTP request
        haunt_id: UUID of the haunt

    Returns:
        RSS XML feed
    """
    # Get haunt and verify ownership
    haunt = get_object_or_404(Haunt, id=haunt_id, owner=request.user)

    # Generate RSS feed
    service = RSSService()
    feed_xml = service.generate_rss_feed(haunt)

    # Return XML response
    return HttpResponse(
        feed_xml,
        content_type='application/rss+xml; charset=utf-8'
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def public_rss_feed(request, public_slug):
    """
    Serve public RSS feed accessible to anyone.

    Args:
        request: HTTP request
        public_slug: Public slug of the haunt

    Returns:
        RSS XML feed
    """
    # Get public haunt
    haunt = get_object_or_404(Haunt, public_slug=public_slug, is_public=True)

    # Generate RSS feed
    service = RSSService()
    feed_xml = service.generate_rss_feed(haunt)

    # Return XML response
    return HttpResponse(
        feed_xml,
        content_type='application/rss+xml; charset=utf-8'
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rss_url(request, haunt_id):
    """
    Get RSS feed URL for a haunt.

    Args:
        request: HTTP request
        haunt_id: UUID of the haunt

    Returns:
        JSON with RSS URL
    """
    # Get haunt and verify ownership
    haunt = get_object_or_404(Haunt, id=haunt_id, owner=request.user)

    # Build RSS URL
    if haunt.is_public and haunt.public_slug:
        rss_url = request.build_absolute_uri(f'/rss/public/{haunt.public_slug}/')
    else:
        rss_url = request.build_absolute_uri(f'/rss/private/{haunt.id}/')

    return Response({
        'rss_url': rss_url,
        'is_public': haunt.is_public
    })