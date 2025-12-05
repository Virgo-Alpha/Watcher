"""
Views for subscription management API
"""
import logging
from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Subscription, UserReadState
from .serializers import (
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
    UserReadStateSerializer,
    BulkReadStateUpdateSerializer
)
from .services import SubscriptionService, ReadStateService
from apps.haunts.models import Haunt
from apps.rss.models import RSSItem

logger = logging.getLogger(__name__)


class SubscriptionPagination(PageNumberPagination):
    """Custom pagination for subscriptions"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user subscriptions to public haunts.
    Provides CRUD operations for subscriptions.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        """Return subscriptions for current user"""
        return SubscriptionService.get_user_subscriptions(self.request.user)

    def list(self, request):
        """
        List all subscriptions for the current user.
        Query params:
        - haunt: Filter by haunt ID
        """
        queryset = self.get_queryset()

        # Filter by haunt
        haunt_id = request.query_params.get('haunt')
        if haunt_id:
            queryset = queryset.filter(haunt_id=haunt_id)

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new subscription.
        Expects: {
            "haunt_id": "uuid",
            "notifications_enabled": true
        }
        """
        logger.info(
            "Subscription create request | User: %s | Content-Type: %s",
            request.user.id if request.user.is_authenticated else 'Anonymous',
            request.content_type
        )
        
        serializer = SubscriptionCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.error(
                "Subscription validation failed | Errors: %s | Data: %s",
                serializer.errors,
                request.data
            )
            serializer.is_valid(raise_exception=True)
        
        # Validation passed
        logger.info("Subscription data validated: %s", serializer.validated_data)

        haunt_id = serializer.validated_data['haunt_id']
        notifications_enabled = serializer.validated_data.get('notifications_enabled', True)

        try:
            haunt = Haunt.objects.get(id=haunt_id)
        except Haunt.DoesNotExist:
            return Response(
                {'error': 'Haunt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            subscription, created = SubscriptionService.subscribe_to_haunt(
                request.user,
                haunt,
                notifications_enabled
            )

            if not created:
                return Response(
                    {'message': 'Already subscribed to this haunt'},
                    status=status.HTTP_200_OK
                )

            logger.info(
                "User %s subscribed to haunt %s",
                request.user.id,
                haunt.id
            )

            response_serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, pk=None):
        """Get subscription details"""
        subscription = self.get_object()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    def update(self, request, pk=None, partial=False):
        """Update subscription (e.g., toggle notifications)"""
        subscription = self.get_object()
        serializer = self.get_serializer(
            subscription,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """Partial update subscription"""
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        """Delete subscription (unsubscribe)"""
        subscription = self.get_object()
        haunt_name = subscription.haunt.name

        subscription.delete()

        logger.info(
            "User %s unsubscribed from haunt %s",
            request.user.id,
            subscription.haunt.id
        )

        return Response(
            {'message': f'Successfully unsubscribed from "{haunt_name}"'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['post'])
    def unsubscribe_by_haunt(self, request):
        """
        Unsubscribe from a haunt by haunt ID.
        Expects: {"haunt_id": "uuid"}
        """
        haunt_id = request.data.get('haunt_id')
        if not haunt_id:
            return Response(
                {'error': 'haunt_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            haunt = Haunt.objects.get(id=haunt_id)
        except Haunt.DoesNotExist:
            return Response(
                {'error': 'Haunt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        deleted_count = SubscriptionService.unsubscribe_from_haunt(
            request.user,
            haunt
        )

        if deleted_count == 0:
            return Response(
                {'message': 'Not subscribed to this haunt'},
                status=status.HTTP_404_NOT_FOUND
            )

        logger.info(
            "User %s unsubscribed from haunt %s",
            request.user.id,
            haunt.id
        )

        return Response(
            {'message': f'Successfully unsubscribed from "{haunt.name}"'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def check_subscription(self, request):
        """
        Check if user is subscribed to a haunt.
        Query params: haunt_id
        """
        haunt_id = request.query_params.get('haunt_id')
        if not haunt_id:
            return Response(
                {'error': 'haunt_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            haunt = Haunt.objects.get(id=haunt_id)
        except Haunt.DoesNotExist:
            return Response(
                {'error': 'Haunt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        is_subscribed = SubscriptionService.is_subscribed(request.user, haunt)

        return Response({
            'haunt_id': str(haunt.id),
            'haunt_name': haunt.name,
            'is_subscribed': is_subscribed
        })

    @action(detail=False, methods=['get'])
    def unread_counts(self, request):
        """
        Get unread counts for all subscribed haunts and folders.
        Returns: {
            "haunts": {"haunt_id": count, ...},
            "folders": {"folder_id": count, ...}
        }
        """
        counts = SubscriptionService.get_unread_counts_for_user(request.user)
        return Response(counts)

    @action(detail=False, methods=['get'])
    def navigation(self, request):
        """
        Get navigation data for subscribed haunts organized by folder.
        Returns a structured navigation tree with folders and haunts.
        Query params:
        - include_owned: Include user's own haunts (default: true)
        """
        from apps.haunts.models import Folder, Haunt
        from apps.haunts.serializers import FolderTreeSerializer, HauntListSerializer

        include_owned = request.query_params.get('include_owned', 'true').lower() in ['true', '1', 'yes']

        # Get subscribed haunts
        subscribed_haunts = Haunt.objects.filter(
            subscriptions__user=request.user
        ).select_related('folder', 'owner')

        # Get owned haunts if requested
        if include_owned:
            owned_haunts = Haunt.objects.filter(
                owner=request.user
            ).select_related('folder', 'owner')

            # Combine owned and subscribed haunts
            all_haunts = owned_haunts.union(subscribed_haunts)
        else:
            all_haunts = subscribed_haunts

        # Get unread counts
        counts = SubscriptionService.get_unread_counts_for_user(request.user)

        # Organize haunts by folder
        haunts_by_folder = {}
        haunts_without_folder = []

        for haunt in all_haunts:
            haunt_data = HauntListSerializer(haunt, context={'request': request}).data
            haunt_data['unread_count'] = counts['haunts'].get(str(haunt.id), 0)

            if haunt.folder_id:
                folder_key = str(haunt.folder_id)
                if folder_key not in haunts_by_folder:
                    haunts_by_folder[folder_key] = []
                haunts_by_folder[folder_key].append(haunt_data)
            else:
                haunts_without_folder.append(haunt_data)

        # Get folder tree
        folders = Folder.objects.filter(
            user=request.user,
            parent=None
        ).prefetch_related('children').order_by('name')

        folder_tree = FolderTreeSerializer(
            folders,
            many=True,
            context={'request': request}
        ).data

        # Add unread counts to folders
        for folder in folder_tree:
            folder['unread_count'] = counts['folders'].get(str(folder['id']), 0)
            folder['haunts'] = haunts_by_folder.get(str(folder['id']), [])

            # Recursively add haunts to child folders
            def add_haunts_to_children(folder_node):
                for child in folder_node.get('children', []):
                    child['unread_count'] = counts['folders'].get(str(child['id']), 0)
                    child['haunts'] = haunts_by_folder.get(str(child['id']), [])
                    add_haunts_to_children(child)

            add_haunts_to_children(folder)

        return Response({
            'folders': folder_tree,
            'haunts_without_folder': haunts_without_folder,
            'total_unread': sum(counts['haunts'].values())
        })


class UserReadStateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user read/starred states for RSS items.
    Provides operations for marking items as read/unread and starred/unstarred.
    """
    serializer_class = UserReadStateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        """Return read states for current user"""
        return UserReadState.objects.filter(
            user=self.request.user
        ).select_related('rss_item', 'rss_item__haunt')

    def list(self, request):
        """
        List read states for the current user.
        Query params:
        - haunt: Filter by haunt ID
        - is_read: Filter by read status (true/false)
        - is_starred: Filter by starred status (true/false)
        """
        queryset = self.get_queryset()

        # Filter by haunt
        haunt_id = request.query_params.get('haunt')
        if haunt_id:
            queryset = queryset.filter(rss_item__haunt_id=haunt_id)

        # Filter by read status
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_read=is_read_bool)

        # Filter by starred status
        is_starred = request.query_params.get('is_starred')
        if is_starred is not None:
            is_starred_bool = is_starred.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_starred=is_starred_bool)

        # Order by most recent first
        queryset = queryset.order_by('-updated_at')

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """
        Mark a single RSS item as read.
        Expects: {"rss_item_id": "uuid"}
        """
        rss_item_id = request.data.get('rss_item_id')
        if not rss_item_id:
            return Response(
                {'error': 'rss_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rss_item = RSSItem.objects.get(id=rss_item_id)
        except RSSItem.DoesNotExist:
            return Response(
                {'error': 'RSS item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        read_state = ReadStateService.mark_as_read(request.user, rss_item)
        serializer = self.get_serializer(read_state)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_unread(self, request):
        """
        Mark a single RSS item as unread.
        Expects: {"rss_item_id": "uuid"}
        """
        rss_item_id = request.data.get('rss_item_id')
        if not rss_item_id:
            return Response(
                {'error': 'rss_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rss_item = RSSItem.objects.get(id=rss_item_id)
        except RSSItem.DoesNotExist:
            return Response(
                {'error': 'RSS item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        read_state = ReadStateService.mark_as_unread(request.user, rss_item)
        serializer = self.get_serializer(read_state)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def toggle_starred(self, request):
        """
        Toggle starred state for an RSS item.
        Expects: {"rss_item_id": "uuid"}
        """
        rss_item_id = request.data.get('rss_item_id')
        if not rss_item_id:
            return Response(
                {'error': 'rss_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rss_item = RSSItem.objects.get(id=rss_item_id)
        except RSSItem.DoesNotExist:
            return Response(
                {'error': 'RSS item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        read_state = ReadStateService.toggle_starred(request.user, rss_item)
        serializer = self.get_serializer(read_state)

        return Response({
            'message': 'Starred' if read_state.is_starred else 'Unstarred',
            'read_state': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def bulk_mark_read(self, request):
        """
        Bulk mark multiple RSS items as read or unread.
        Expects: {
            "rss_item_ids": ["uuid1", "uuid2", ...],
            "is_read": true
        }
        """
        serializer = BulkReadStateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rss_item_ids = serializer.validated_data['rss_item_ids']
        is_read = serializer.validated_data.get('is_read', True)

        # Get RSS items
        rss_items = RSSItem.objects.filter(id__in=rss_item_ids)

        if not rss_items.exists():
            return Response(
                {'error': 'No RSS items found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if is_read:
            # Bulk mark as read
            ReadStateService.bulk_mark_read(request.user, rss_items)
            message = f'Marked {rss_items.count()} items as read'
        else:
            # Mark as unread one by one (no bulk unread method)
            for item in rss_items:
                ReadStateService.mark_as_unread(request.user, item)
            message = f'Marked {rss_items.count()} items as unread'

        logger.info(
            "User %s bulk updated %d items to is_read=%s",
            request.user.id,
            rss_items.count(),
            is_read
        )

        return Response({
            'message': message,
            'updated_count': rss_items.count()
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def starred_items(self, request):
        """
        Get all starred items for the current user.
        Query params:
        - haunt: Filter by haunt ID
        """
        haunt_id = request.query_params.get('haunt')
        haunt = None

        if haunt_id:
            try:
                haunt = Haunt.objects.get(id=haunt_id)
            except Haunt.DoesNotExist:
                return Response(
                    {'error': 'Haunt not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        starred_states = ReadStateService.get_starred_items(request.user, haunt)

        # Paginate results
        page = self.paginate_queryset(starred_states)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(starred_states, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_items(self, request):
        """
        Get all unread items for the current user.
        Query params:
        - haunt: Filter by haunt ID
        """
        haunt_id = request.query_params.get('haunt')
        haunt = None

        if haunt_id:
            try:
                haunt = Haunt.objects.get(id=haunt_id)
            except Haunt.DoesNotExist:
                return Response(
                    {'error': 'Haunt not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        unread_items = ReadStateService.get_unread_items(request.user, haunt)

        # Paginate results
        page = self.paginate_queryset(unread_items)
        if page is not None:
            # Serialize RSS items directly
            from apps.rss.serializers import RSSItemSerializer
            serializer = RSSItemSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        from apps.rss.serializers import RSSItemSerializer
        serializer = RSSItemSerializer(unread_items, many=True, context={'request': request})
        return Response(serializer.data)