"""
Views for haunt management API including folders, haunts, and UI preferences.
"""
import logging
import ipaddress
import socket
from collections import defaultdict
from urllib.parse import urlparse

from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Folder, Haunt, UserUIPreferences
from .serializers import (
    FolderSerializer, FolderTreeSerializer, UserUIPreferencesSerializer,
    HauntSerializer, HauntListSerializer, HauntCreateWithAISerializer
)
from .validators import URLSecurityValidator
from apps.ai.services import AIConfigService, AIConfigurationError
from apps.scraping.services import ScrapingService, ScrapingError

logger = logging.getLogger(__name__)


def validate_url_security(url: str) -> tuple[bool, str]:
    """
    Comprehensive SSRF protection for user-provided URLs.
    
    Returns: (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)
        
        # Only allow HTTP and HTTPS schemes
        if parsed.scheme not in ['http', 'https']:
            return False, 'Only HTTP and HTTPS URLs are allowed'
        
        hostname = parsed.hostname
        if not hostname:
            return False, 'Invalid URL: missing hostname'
        
        # Block common localhost representations
        localhost_names = [
            'localhost', '127.0.0.1', '0.0.0.0', 
            '::1', '::', '0:0:0:0:0:0:0:1', '0000:0000:0000:0000:0000:0000:0000:0001'
        ]
        if hostname.lower() in localhost_names:
            return False, 'Access to localhost is not allowed'
        
        # Resolve hostname to IP and check if it's private
        try:
            # Get all IP addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None)
            for info in addr_info:
                ip_str = info[4][0]
                try:
                    ip = ipaddress.ip_address(ip_str)
                    # Block private, loopback, link-local, reserved, and multicast IPs
                    if (ip.is_private or ip.is_loopback or ip.is_link_local or 
                        ip.is_reserved or ip.is_multicast):
                        return False, 'Access to private/internal IP addresses is not allowed'
                    
                    # Block cloud metadata endpoints (AWS, GCP, Azure)
                    if ip_str.startswith('169.254.'):
                        return False, 'Access to cloud metadata endpoints is not allowed'
                        
                except ValueError:
                    continue
                    
        except socket.gaierror:
            return False, 'Unable to resolve hostname'
        except Exception as e:
            logger.error("DNS resolution error during URL validation: %s", str(e))
            return False, 'URL validation failed'
        
        return True, ''
        
    except Exception as e:
        logger.error("URL parsing error: %s", str(e))
        return False, 'Invalid URL format'


class FolderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing folder hierarchy.
    Provides CRUD operations and tree retrieval.
    """
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for folders
    
    def get_queryset(self):
        """Return folders owned by current user"""
        return Folder.objects.filter(user=self.request.user).select_related('parent')
    
    def get_serializer_class(self):
        """Use tree serializer for tree action"""
        if self.action == 'tree':
            return FolderTreeSerializer
        return FolderSerializer
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get folder tree with nested structure.
        Returns only root folders with their children nested.
        """
        # Prefetch all descendants in one query to avoid N+1
        root_folders = (
            self.get_queryset()
            .filter(parent=None)
            .prefetch_related(
                Prefetch('children', queryset=Folder.objects.prefetch_related('children'))
            )
            .order_by('name')
        )
        serializer = self.get_serializer(root_folders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_haunts(self, request, pk=None):
        """
        Assign multiple haunts to this folder.
        Expects: {"haunt_ids": [list of haunt UUIDs]}
        """
        folder = self.get_object()
        haunt_ids = request.data.get('haunt_ids', [])
        
        if not isinstance(haunt_ids, list):
            return Response(
                {'error': 'haunt_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate all haunts belong to current user using count() to avoid fetching objects
        haunt_count = Haunt.objects.filter(
            id__in=haunt_ids,
            owner=request.user
        ).count()
        
        if haunt_count != len(haunt_ids):
            return Response(
                {'error': 'Some haunts not found or not owned by user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assign haunts to folder
        with transaction.atomic():
            updated = Haunt.objects.filter(
                id__in=haunt_ids,
                owner=request.user
            ).update(folder=folder)
        
        return Response({
            'message': f'Successfully assigned {updated} haunts to folder',
            'assigned_count': updated
        })
    
    @action(detail=True, methods=['post'])
    def unassign_haunts(self, request, pk=None):
        """
        Remove haunts from this folder (set folder to None).
        Expects: {"haunt_ids": [list of haunt UUIDs]}
        """
        folder = self.get_object()
        haunt_ids = request.data.get('haunt_ids', [])
        
        if not isinstance(haunt_ids, list):
            return Response(
                {'error': 'haunt_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Unassign haunts from folder directly without fetching
        with transaction.atomic():
            unassigned_count = Haunt.objects.filter(
                id__in=haunt_ids,
                owner=request.user,
                folder=folder
            ).update(folder=None)
        
        return Response({
            'message': f'Successfully unassigned {unassigned_count} haunts from folder',
            'unassigned_count': unassigned_count
        })
    
    def perform_create(self, serializer):
        """Set current user as folder owner"""
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        """
        Delete folder and move its haunts to parent folder or None.
        """
        with transaction.atomic():
            # Move haunts to parent folder or None
            instance.haunts.update(folder=instance.parent)
            
            # Move child folders to parent folder or None
            instance.children.update(parent=instance.parent)
            
            # Delete the folder
            instance.delete()


class UserUIPreferencesViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user UI preferences.
    Each user has only one preferences object.
    """
    serializer_class = UserUIPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for preferences
    
    def get_queryset(self):
        """Return preferences for current user"""
        return UserUIPreferences.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create preferences for current user"""
        preferences, created = UserUIPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences
    
    def list(self, request):
        """Return current user's preferences"""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    def create(self, request):
        """Not allowed - preferences are auto-created"""
        return Response(
            {'error': 'Preferences are automatically created. Use PUT to update.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, pk=None, partial=False):
        """Update user preferences"""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        """Partial update user preferences"""
        return self.update(request, pk, partial=True)
    
    def destroy(self, request, pk=None):
        """Reset preferences to defaults"""
        preferences = self.get_object()
        preferences.delete()
        # Get new default preferences
        new_preferences = self.get_object()
        serializer = self.get_serializer(new_preferences)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def toggle_folder_collapsed(self, request):
        """
        Toggle folder collapsed state.
        Expects: {"folder_id": folder_id}
        """
        folder_id = request.data.get('folder_id')
        if not folder_id:
            return Response(
                {'error': 'folder_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate folder belongs to user
        try:
            folder = Folder.objects.get(id=folder_id, user=request.user)
        except Folder.DoesNotExist:
            return Response(
                {'error': 'Folder not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        preferences = self.get_object()
        preferences.toggle_folder_collapsed(folder_id)
        
        return Response({
            'message': 'Folder collapsed state toggled',
            'is_collapsed': preferences.is_folder_collapsed(folder_id)
        })


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a haunt to edit it.
    Public haunts are readable by anyone.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for public haunts
        if request.method in permissions.SAFE_METHODS:
            if obj.is_public:
                return True
            # Private haunts only accessible by owner
            return obj.owner == request.user

        # Write permissions are only allowed to the owner
        return obj.owner == request.user


class HauntPagination(PageNumberPagination):
    """Custom pagination for haunts"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class HauntViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing haunts with CRUD operations.
    Provides owner-only access to private haunts and folder support.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = HauntPagination

    def get_queryset(self):
        """
        Return haunts based on user permissions.
        - Authenticated users see their own haunts
        - Public haunts are visible to all authenticated users
        """
        user = self.request.user
        if user.is_authenticated:
            # Return user's own haunts plus public haunts they might want to view
            return Haunt.objects.filter(owner=user).select_related('folder', 'owner')
        return Haunt.objects.none()

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return HauntListSerializer
        return HauntSerializer

    def list(self, request):
        """
        List haunts with optional filtering by folder.
        Query params:
        - folder: Filter by folder ID (use 'none' for haunts without folder)
        - is_active: Filter by active status (true/false)
        """
        queryset = self.get_queryset()

        # Filter by folder
        folder_param = request.query_params.get('folder')
        if folder_param:
            if folder_param.lower() == 'none':
                queryset = queryset.filter(folder=None)
            else:
                queryset = queryset.filter(folder_id=folder_param)

        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)

        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create a new haunt"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Get haunt details"""
        haunt = self.get_object()
        serializer = self.get_serializer(haunt)
        return Response(serializer.data)

    def update(self, request, pk=None, partial=False):
        """Update haunt"""
        haunt = self.get_object()
        serializer = self.get_serializer(haunt, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """Partial update haunt"""
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        """Delete haunt"""
        haunt = self.get_object()
        self.perform_destroy(haunt)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """Set current user as haunt owner"""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def move_to_folder(self, request, pk=None):
        """
        Move haunt to a different folder.
        Expects: {"folder_id": folder_id or null}
        """
        haunt = self.get_object()
        folder_id = request.data.get('folder_id')

        if folder_id is None:
            # Remove from folder
            haunt.folder = None
            haunt.save(update_fields=['folder'])
            return Response({
                'message': 'Haunt removed from folder',
                'folder': None
            })

        # Validate folder exists and belongs to user
        try:
            folder = Folder.objects.get(id=folder_id, user=request.user)
        except Folder.DoesNotExist:
            return Response(
                {'error': 'Folder not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        haunt.folder = folder
        haunt.save(update_fields=['folder'])

        return Response({
            'message': f'Haunt moved to folder "{folder.name}"',
            'folder': FolderSerializer(folder).data
        })

    @action(detail=False, methods=['get'])
    def by_folder(self, request):
        """
        Get haunts grouped by folder.
        Returns a dictionary with folder IDs as keys and lists of haunts as values.
        Includes a 'null' key for haunts without a folder.
        """
        queryset = self.get_queryset().prefetch_related('folder')

        # Group haunts by folder_id first (avoid N+1)
        grouped_haunts = defaultdict(list)
        for haunt in queryset:
            folder_key = str(haunt.folder_id) if haunt.folder_id else 'null'
            grouped_haunts[folder_key].append(haunt)

        # Serialize each group in batch
        grouped = {}
        for folder_key, haunts in grouped_haunts.items():
            grouped[folder_key] = HauntListSerializer(
                haunts, many=True, context={'request': request}
            ).data

        return Response(grouped)

    @action(detail=False, methods=['get'])
    def unread_counts(self, request):
        """
        Get unread counts for all haunts and folders.
        Returns: {
            "haunts": {"haunt_id": count, ...},
            "folders": {"folder_id": count, ...}
        }
        """
        from apps.subscriptions.services import SubscriptionService
        counts = SubscriptionService.get_unread_counts_for_user(request.user)
        return Response(counts)

    @action(detail=False, methods=['post'])
    def create_with_ai(self, request):
        """
        Create a haunt using AI to generate configuration from natural language.
        Expects: {
            "url": "https://example.com",
            "description": "Monitor the admission status",
            "name": "Optional name",
            "folder": "Optional folder ID",
            "scrape_interval": 60,
            "alert_mode": "on_change"
        }
        """
        serializer = HauntCreateWithAISerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        url = serializer.validated_data['url']
        description = serializer.validated_data['description']
        name = serializer.validated_data.get('name')
        folder = serializer.validated_data.get('folder')
        scrape_interval = serializer.validated_data.get('scrape_interval', 60)
        alert_mode = serializer.validated_data.get('alert_mode', 'on_change')

        # Validate URL to prevent SSRF attacks
        is_valid, error_msg = validate_url_security(url)
        if not is_valid:
            return Response({
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate name from URL if not provided
        if not name:
            parsed = urlparse(url)
            name = parsed.netloc or 'New Haunt'

        # Initialize AI service
        ai_service = AIConfigService()

        if not ai_service.is_available():
            return Response({
                'error': 'AI service is not available. Please configure LLM_API_KEY.',
                'fallback': 'You can create a haunt manually with custom configuration.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            # Generate configuration using AI
            logger.info("Generating AI configuration for URL: %s", url)
            config = ai_service.generate_config(url, description)

            # Create the haunt
            haunt = Haunt.objects.create(
                owner=request.user,
                name=name,
                url=url,
                description=description,
                config=config,
                folder=folder,
                scrape_interval=scrape_interval,
                alert_mode=alert_mode
            )

            logger.info("Successfully created haunt with AI: %s", haunt.id)

            # Return the created haunt
            haunt_serializer = HauntSerializer(haunt, context={'request': request})
            return Response(haunt_serializer.data, status=status.HTTP_201_CREATED)

        except AIConfigurationError as e:
            logger.error("AI configuration generation failed: %s", str(e))
            return Response({
                'error': str(e),
                'fallback': 'You can create a haunt manually with custom configuration.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Unexpected error during AI haunt creation: %s", str(e))
            return Response({
                'error': 'An unexpected error occurred during haunt creation.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def test_scrape(self, request):
        """
        Perform a test scrape for preview purposes without creating a haunt.
        Expects: {
            "url": "https://example.com",
            "config": {
                "selectors": {...},
                "normalization": {...},
                "truthy_values": {...}
            }
        }
        Returns extracted data for preview.
        """
        url = request.data.get('url')
        config = request.data.get('config')

        if not url:
            return Response({
                'error': 'URL is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate URL to prevent SSRF attacks
        is_valid, error_msg = validate_url_security(url)
        if not is_valid:
            return Response({
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)

        if not config:
            return Response({
                'error': 'Configuration is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate config structure
        required_keys = ['selectors', 'normalization', 'truthy_values']
        for key in required_keys:
            if key not in config:
                return Response({
                    'error': f'Configuration must include "{key}" key'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize scraping service
        scraping_service = ScrapingService()

        try:
            logger.info("Performing test scrape for URL: %s", url)

            # Perform the scrape
            extracted_data = scraping_service.scrape_url(url, config)

            logger.info("Test scrape successful for URL: %s", url)

            return Response({
                'success': True,
                'url': url,
                'extracted_data': extracted_data,
                'message': 'Test scrape completed successfully'
            }, status=status.HTTP_200_OK)

        except ScrapingError as e:
            logger.error("Test scrape failed: %s", str(e))
            return Response({
                'error': str(e),
                'url': url
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Unexpected error during test scrape: %s", str(e))
            return Response({
                'error': 'An unexpected error occurred during test scrape'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def generate_config_preview(self, request):
        """
        Generate configuration from natural language without creating a haunt.
        Useful for the setup wizard preview step.
        Expects: {
            "url": "https://example.com",
            "description": "Monitor the admission status"
        }
        Returns generated configuration for preview.
        """
        url = request.data.get('url')
        description = request.data.get('description')

        if not url:
            return Response({
                'error': 'URL is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate URL to prevent SSRF attacks
        is_valid, error_msg = validate_url_security(url)
        if not is_valid:
            return Response({
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)

        if not description:
            return Response({
                'error': 'Description is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize AI service
        ai_service = AIConfigService()

        if not ai_service.is_available():
            return Response({
                'error': 'AI service is not available. Please configure LLM_API_KEY.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            logger.info("Generating config preview for URL: %s", url)

            # Generate configuration
            config = ai_service.generate_config(url, description)

            logger.info("Config preview generated successfully for URL: %s", url)

            return Response({
                'success': True,
                'url': url,
                'description': description,
                'config': config,
                'message': 'Configuration generated successfully'
            }, status=status.HTTP_200_OK)

        except AIConfigurationError as e:
            logger.error("Config preview generation failed: %s", str(e))
            return Response({
                'error': 'Failed to generate configuration. Please try a different description.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Unexpected error during config preview")
            return Response({
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def make_public(self, request, pk=None):
        """
        Make a haunt public and generate a public_slug.
        Only the owner can make their haunt public.
        Returns the updated haunt with public_slug.
        """
        haunt = self.get_object()

        if haunt.is_public:
            return Response({
                'message': 'Haunt is already public',
                'public_slug': haunt.public_slug,
                'public_url': haunt.get_public_url()
            }, status=status.HTTP_200_OK)

        # Make haunt public (save method will generate public_slug)
        haunt.is_public = True
        haunt.save()

        logger.info("Haunt %s made public with slug: %s", haunt.id, haunt.public_slug)

        serializer = self.get_serializer(haunt)
        return Response({
            'message': 'Haunt successfully made public',
            'haunt': serializer.data,
            'public_slug': haunt.public_slug,
            'public_url': haunt.get_public_url()
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def make_private(self, request, pk=None):
        """
        Make a public haunt private again.
        Only the owner can make their haunt private.
        Removes the public_slug.
        """
        haunt = self.get_object()

        if not haunt.is_public:
            return Response({
                'message': 'Haunt is already private'
            }, status=status.HTTP_200_OK)

        # Make haunt private (save method will clear public_slug)
        haunt.is_public = False
        haunt.save()

        logger.info("Haunt %s made private", haunt.id)

        serializer = self.get_serializer(haunt)
        return Response({
            'message': 'Haunt successfully made private',
            'haunt': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """
        Manually trigger an immediate scrape for this haunt.
        Implements rate limiting to prevent abuse.
        Only the owner can manually refresh their haunt.
        """
        from apps.scraping.tasks import scrape_haunt_manual
        from django.core.cache import cache

        haunt = self.get_object()

        # Rate limiting: max 1 manual refresh per 5 minutes per haunt
        cache_key = f'manual_refresh_{haunt.id}'
        last_refresh = cache.get(cache_key)

        if last_refresh:
            return Response({
                'error': 'Rate limit exceeded. Please wait before refreshing again.',
                'retry_after_seconds': 300  # 5 minutes
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Set rate limit cache (5 minutes)
        cache.set(cache_key, timezone.now().isoformat(), 300)

        # Trigger manual scrape task
        try:
            task = scrape_haunt_manual.delay(str(haunt.id))

            logger.info(
                "Manual refresh triggered for haunt %s by user %s. Task ID: %s",
                haunt.id,
                request.user.id,
                task.id
            )

            return Response({
                'message': 'Scrape initiated successfully',
                'task_id': task.id,
                'haunt_id': str(haunt.id),
                'status': 'pending'
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            logger.error("Failed to trigger manual refresh for haunt %s: %s", haunt.id, e)
            return Response({
                'error': 'Failed to initiate scrape',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def scrape_status(self, request, pk=None):
        """
        Get the current scraping status for this haunt.
        Returns information about last scrape and any ongoing operations.
        """
        haunt = self.get_object()

        # Check if there's an active scrape task
        from django.core.cache import cache
        cache_key = f'manual_refresh_{haunt.id}'
        is_rate_limited = cache.get(cache_key) is not None

        response_data = {
            'haunt_id': str(haunt.id),
            'last_scraped_at': haunt.last_scraped_at.isoformat() if haunt.last_scraped_at else None,
            'is_active': haunt.is_active,
            'error_count': haunt.error_count,
            'last_error': haunt.last_error,
            'is_healthy': haunt.is_healthy,
            'is_rate_limited': is_rate_limited,
            'scrape_interval': haunt.scrape_interval,
            'scrape_interval_display': haunt.scrape_interval_display
        }

        # Calculate time until next scheduled scrape
        if haunt.last_scraped_at:
            from datetime import timedelta
            next_scrape_time = haunt.last_scraped_at + timedelta(minutes=haunt.scrape_interval)
            time_until_next = (next_scrape_time - timezone.now()).total_seconds()

            if time_until_next > 0:
                response_data['next_scrape_in_seconds'] = int(time_until_next)
                response_data['next_scrape_at'] = next_scrape_time.isoformat()
            else:
                response_data['next_scrape_in_seconds'] = 0
                response_data['next_scrape_at'] = 'pending'

        return Response(response_data)


class PublicHauntViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for public haunt directory and detail views.
    Accessible without authentication.
    """
    serializer_class = HauntSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = HauntPagination
    lookup_field = 'public_slug'

    def get_queryset(self):
        """Return only public haunts"""
        return Haunt.objects.filter(
            is_public=True,
            is_active=True
        ).select_related('folder', 'owner').order_by('-created_at')

    def list(self, request):
        """
        List all public haunts in the directory.
        Query params:
        - search: Search in name, description, or URL
        - owner: Filter by owner username
        """
        queryset = self.get_queryset()

        # Search functionality
        search_query = request.query_params.get('search')
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(url__icontains=search_query)
            )

        # Filter by owner
        owner_username = request.query_params.get('owner')
        if owner_username:
            queryset = queryset.filter(owner__username=owner_username)

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, public_slug=None):
        """
        Get public haunt details by public_slug.
        Accessible without authentication.
        """
        try:
            haunt = self.get_queryset().get(public_slug=public_slug)
        except Haunt.DoesNotExist:
            return Response({
                'error': 'Public haunt not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(haunt)
        return Response(serializer.data)