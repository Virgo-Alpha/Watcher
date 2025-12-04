"""
Subscription service business logic
"""
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Subscription, UserReadState
from apps.rss.models import RSSItem
from apps.haunts.models import Haunt, Folder


class SubscriptionService:
    """Service for managing subscriptions and read states"""

    @staticmethod
    def get_user_subscriptions(user):
        """Get all subscriptions for a user with haunt details"""
        return Subscription.objects.filter(
            user=user
        ).select_related(
            'haunt',
            'haunt__owner',
            'haunt__folder'
        ).order_by('-subscribed_at')

    @staticmethod
    def subscribe_to_haunt(user, haunt, notifications_enabled=True):
        """
        Subscribe user to a haunt.
        Returns (subscription, created) tuple.
        """
        # Validate haunt is public
        if not haunt.is_public:
            raise ValueError("Can only subscribe to public haunts")

        # Prevent self-subscription
        if haunt.owner == user:
            raise ValueError("Cannot subscribe to your own haunt")

        subscription, created = Subscription.objects.get_or_create(
            user=user,
            haunt=haunt,
            defaults={'notifications_enabled': notifications_enabled}
        )

        return subscription, created

    @staticmethod
    def unsubscribe_from_haunt(user, haunt):
        """
        Unsubscribe user from a haunt.
        Returns number of subscriptions deleted.
        """
        return Subscription.objects.filter(
            user=user,
            haunt=haunt
        ).delete()[0]

    @staticmethod
    def is_subscribed(user, haunt):
        """Check if user is subscribed to a haunt"""
        return Subscription.objects.filter(
            user=user,
            haunt=haunt
        ).exists()

    @staticmethod
    def get_unread_count_for_haunt(user, haunt):
        """Get unread count for a specific haunt"""
        # Get all RSS items for this haunt
        rss_items = RSSItem.objects.filter(haunt=haunt)

        # Get read states for this user
        read_item_ids = UserReadState.objects.filter(
            user=user,
            rss_item__in=rss_items,
            is_read=True
        ).values_list('rss_item_id', flat=True)

        # Count unread items
        return rss_items.exclude(id__in=read_item_ids).count()

    @staticmethod
    def get_unread_counts_for_user(user):
        """
        Get unread counts for all haunts and folders for a user.
        Returns dict with 'haunts' and 'folders' keys.
        """
        # Get all haunts user owns or is subscribed to
        owned_haunts = Haunt.objects.filter(owner=user)
        subscribed_haunts = Haunt.objects.filter(
            subscriptions__user=user
        )
        all_haunts = owned_haunts.union(subscribed_haunts)

        # Get all RSS items for these haunts
        rss_items = RSSItem.objects.filter(haunt__in=all_haunts)

        # Get read states for this user
        read_item_ids = set(
            UserReadState.objects.filter(
                user=user,
                rss_item__in=rss_items,
                is_read=True
            ).values_list('rss_item_id', flat=True)
        )

        # Calculate unread counts per haunt
        haunt_counts = {}
        for haunt in all_haunts:
            haunt_items = rss_items.filter(haunt=haunt)
            unread = sum(1 for item in haunt_items if item.id not in read_item_ids)
            haunt_counts[str(haunt.id)] = unread

        # Calculate unread counts per folder
        folder_counts = {}
        folders = Folder.objects.filter(user=user)
        for folder in folders:
            folder_haunts = all_haunts.filter(folder=folder)
            folder_unread = sum(
                haunt_counts.get(str(haunt.id), 0)
                for haunt in folder_haunts
            )
            folder_counts[str(folder.id)] = folder_unread

        return {
            'haunts': haunt_counts,
            'folders': folder_counts
        }


class ReadStateService:
    """Service for managing read/starred states"""

    @staticmethod
    def mark_as_read(user, rss_item):
        """Mark a single RSS item as read"""
        read_state, created = UserReadState.objects.get_or_create(
            user=user,
            rss_item=rss_item,
            defaults={'is_read': True, 'read_at': timezone.now()}
        )

        if not created and not read_state.is_read:
            read_state.mark_read()

        return read_state

    @staticmethod
    def mark_as_unread(user, rss_item):
        """Mark a single RSS item as unread"""
        read_state, created = UserReadState.objects.get_or_create(
            user=user,
            rss_item=rss_item,
            defaults={'is_read': False}
        )

        if not created and read_state.is_read:
            read_state.mark_unread()

        return read_state

    @staticmethod
    def toggle_starred(user, rss_item):
        """Toggle starred state for an RSS item"""
        read_state, created = UserReadState.objects.get_or_create(
            user=user,
            rss_item=rss_item
        )

        read_state.toggle_starred()
        return read_state

    @staticmethod
    def bulk_mark_read(user, rss_items):
        """Bulk mark multiple RSS items as read"""
        return UserReadState.bulk_mark_read(user, rss_items)

    @staticmethod
    def get_read_state(user, rss_item):
        """Get read state for a specific RSS item"""
        try:
            return UserReadState.objects.get(user=user, rss_item=rss_item)
        except UserReadState.DoesNotExist:
            return None

    @staticmethod
    def get_starred_items(user, haunt=None):
        """Get all starred items for a user, optionally filtered by haunt"""
        queryset = UserReadState.objects.filter(
            user=user,
            is_starred=True
        ).select_related('rss_item', 'rss_item__haunt')

        if haunt:
            queryset = queryset.filter(rss_item__haunt=haunt)

        return queryset.order_by('-starred_at')

    @staticmethod
    def get_unread_items(user, haunt=None):
        """Get all unread items for a user, optionally filtered by haunt"""
        # Get all RSS items
        rss_items = RSSItem.objects.all()
        if haunt:
            rss_items = rss_items.filter(haunt=haunt)

        # Get read item IDs
        read_item_ids = UserReadState.objects.filter(
            user=user,
            is_read=True
        ).values_list('rss_item_id', flat=True)

        # Return unread items
        return rss_items.exclude(id__in=read_item_ids).order_by('-pub_date')