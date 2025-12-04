"""
Serializers for subscription management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Subscription, UserReadState
from apps.haunts.serializers import HauntListSerializer
from apps.rss.models import RSSItem

User = get_user_model()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription with haunt details"""

    haunt_details = HauntListSerializer(source='haunt', read_only=True)
    haunt_name = serializers.CharField(source='haunt.name', read_only=True)
    haunt_url = serializers.URLField(source='haunt.url', read_only=True)
    owner_username = serializers.CharField(source='haunt.owner.username', read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'haunt', 'haunt_details', 'haunt_name', 'haunt_url',
            'owner_username', 'subscribed_at', 'notifications_enabled',
            'unread_count'
        ]
        read_only_fields = ['id', 'subscribed_at']

    def get_unread_count(self, obj):
        """Get count of unread RSS items for this subscription"""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return 0

        # Get all RSS items for this haunt
        rss_items = RSSItem.objects.filter(haunt=obj.haunt)

        # Get read states for this user
        read_item_ids = UserReadState.objects.filter(
            user=user,
            rss_item__in=rss_items,
            is_read=True
        ).values_list('rss_item_id', flat=True)

        # Count unread items
        return rss_items.exclude(id__in=read_item_ids).count()

    def validate_haunt(self, value):
        """Validate haunt is public"""
        if not value.is_public:
            raise serializers.ValidationError(
                "Can only subscribe to public haunts."
            )
        return value

    def validate(self, attrs):
        """Validate subscription doesn't already exist"""
        request = self.context.get('request')
        if request and not self.instance:
            haunt = attrs.get('haunt')
            if haunt and Subscription.objects.filter(
                user=request.user,
                haunt=haunt
            ).exists():
                raise serializers.ValidationError(
                    "You are already subscribed to this haunt."
                )

            # Prevent self-subscription
            if haunt and haunt.owner == request.user:
                raise serializers.ValidationError(
                    "Cannot subscribe to your own haunt."
                )

        return attrs


class SubscriptionCreateSerializer(serializers.Serializer):
    """Serializer for creating subscriptions"""

    haunt_id = serializers.UUIDField(required=True, help_text="UUID of the haunt to subscribe to")
    notifications_enabled = serializers.BooleanField(
        default=True,
        help_text="Enable notifications for this subscription"
    )

    def validate_haunt_id(self, value):
        """Validate haunt exists and is public"""
        from apps.haunts.models import Haunt

        try:
            haunt = Haunt.objects.get(id=value)
        except Haunt.DoesNotExist:
            raise serializers.ValidationError("Haunt not found.")

        if not haunt.is_public:
            raise serializers.ValidationError("Can only subscribe to public haunts.")

        # Prevent self-subscription
        request = self.context.get('request')
        if request and haunt.owner == request.user:
            raise serializers.ValidationError("Cannot subscribe to your own haunt.")

        return value


class UserReadStateSerializer(serializers.ModelSerializer):
    """Serializer for user read state"""

    rss_item_title = serializers.CharField(source='rss_item.title', read_only=True)
    haunt_id = serializers.UUIDField(source='rss_item.haunt.id', read_only=True)
    haunt_name = serializers.CharField(source='rss_item.haunt.name', read_only=True)

    class Meta:
        model = UserReadState
        fields = [
            'id', 'rss_item', 'rss_item_title', 'haunt_id', 'haunt_name',
            'is_read', 'is_starred', 'read_at', 'starred_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'read_at', 'starred_at', 'created_at', 'updated_at']


class BulkReadStateUpdateSerializer(serializers.Serializer):
    """Serializer for bulk read state updates"""

    rss_item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="List of RSS item UUIDs to mark as read"
    )
    is_read = serializers.BooleanField(
        default=True,
        help_text="Mark as read (true) or unread (false)"
    )