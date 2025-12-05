from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Folder, Haunt, UserUIPreferences

User = get_user_model()


class FolderSerializer(serializers.ModelSerializer):
    """Serializer for Folder model with basic fields"""
    
    full_path = serializers.ReadOnlyField()
    depth = serializers.ReadOnlyField()
    haunt_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'parent', 'full_path', 'depth',
            'haunt_count', 'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_haunt_count(self, obj):
        """Get count of haunts in this folder"""
        return obj.haunts.count()
    
    def get_unread_count(self, obj):
        """Get count of unread items in this folder's haunts"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        from apps.subscriptions.services import SubscriptionService
        counts = SubscriptionService.get_unread_counts_for_user(request.user)
        return counts['folders'].get(str(obj.id), 0)
    
    def validate_parent(self, value):
        """Validate parent folder belongs to same user"""
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError(
                "Parent folder must belong to the same user."
            )
        return value
    
    def create(self, validated_data):
        """Create folder with current user as owner"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FolderTreeSerializer(serializers.ModelSerializer):
    """Serializer for folder tree with nested children"""
    
    children = serializers.SerializerMethodField()
    full_path = serializers.ReadOnlyField()
    depth = serializers.ReadOnlyField()
    haunt_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'parent', 'children', 'full_path', 'depth',
            'haunt_count', 'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """Get nested children folders"""
        children = obj.children.all().order_by('name')
        return FolderTreeSerializer(children, many=True, context=self.context).data
    
    def get_haunt_count(self, obj):
        """Get count of haunts in this folder and all descendants"""
        count = obj.haunts.count()
        for child in obj.children.all():
            count += self.get_haunt_count(child)
        return count
    
    def get_unread_count(self, obj):
        """Get count of unread items in this folder and all descendants"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        from apps.subscriptions.services import SubscriptionService
        counts = SubscriptionService.get_unread_counts_for_user(request.user)

        # Get count for this folder
        total = counts['folders'].get(str(obj.id), 0)

        # Add counts for all descendant folders
        for child in obj.children.all():
            total += self.get_unread_count(child)

        return total


class UserUIPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user UI preferences"""
    
    class Meta:
        model = UserUIPreferences
        fields = [
            'left_panel_width', 'middle_panel_width', 'keyboard_shortcuts_enabled',
            'auto_mark_read_on_scroll', 'auto_mark_read_on_open', 'collapsed_folders',
            'items_per_page', 'show_read_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HauntSerializer(serializers.ModelSerializer):
    """Serializer for Haunt model with nested configuration and folder handling"""
    
    folder_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    scrape_interval_display = serializers.ReadOnlyField()
    is_healthy = serializers.ReadOnlyField()
    public_url = serializers.SerializerMethodField()
    rss_url = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Haunt
        fields = [
            'id', 'name', 'url', 'description', 'config', 'current_state',
            'last_alert_state', 'scrape_interval', 'scrape_interval_display',
            'enable_ai_summary', 'is_public', 'public_slug', 'is_active',
            'last_scraped_at', 'last_error', 'error_count', 'is_healthy',
            'folder', 'folder_name', 'unread_count', 'public_url', 'rss_url',
            'is_subscribed', 'owner_email', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'public_slug', 'last_scraped_at', 'last_error', 'error_count',
            'created_at', 'updated_at'
        ]
    
    def get_folder_name(self, obj):
        """Get folder name if haunt is in a folder"""
        return obj.folder.name if obj.folder else None
    
    def get_unread_count(self, obj):
        """Get count of unread RSS items for this haunt"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        from apps.subscriptions.services import SubscriptionService
        return SubscriptionService.get_unread_count_for_haunt(request.user, obj)
    
    def get_public_url(self, obj):
        """Get public URL for this haunt if it's public"""
        return obj.get_public_url()
    
    def get_rss_url(self, obj):
        """Get RSS feed URL for this haunt"""
        request = self.context.get('request')
        return obj.get_rss_url(request)
    
    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this haunt (vs owning it)"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # If user owns the haunt, they're not subscribed
        if obj.owner == request.user:
            return False
        
        # Use prefetched subscriptions if available to avoid N+1 queries
        if hasattr(obj, 'user_subscriptions_cache'):
            return len(obj.user_subscriptions_cache) > 0
        
        # Fallback to query if not prefetched (e.g., single object retrieval)
        from apps.subscriptions.models import Subscription
        return Subscription.objects.filter(user=request.user, haunt=obj).exists()
    
    def get_owner_email(self, obj):
        """Get owner email for subscribed haunts"""
        return obj.owner.email if obj.owner else None
    
    def validate_folder(self, value):
        """Validate folder belongs to same user"""
        if value:
            request = self.context.get('request')
            if request and value.user != request.user:
                raise serializers.ValidationError(
                    "Folder must belong to the same user."
                )
        return value
    
    def validate_config(self, value):
        """Validate configuration structure"""
        if value and value != {}:
            required_keys = ['selectors', 'normalization']
            for key in required_keys:
                if key not in value:
                    raise serializers.ValidationError(
                        f'Configuration must include "{key}" key.'
                    )
        return value
    
    def validate_scrape_interval(self, value):
        """Validate scrape interval is one of allowed values"""
        allowed_intervals = [choice[0] for choice in Haunt.SCRAPE_INTERVALS]
        if value not in allowed_intervals:
            raise serializers.ValidationError(
                f'Scrape interval must be one of: {allowed_intervals}'
            )
        return value
    
    def create(self, validated_data):
        """Create haunt with current user as owner"""
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)


class HauntListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for haunt list views"""
    
    folder_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    scrape_interval_display = serializers.ReadOnlyField()
    is_healthy = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Haunt
        fields = [
            'id', 'name', 'url', 'is_public', 'is_active', 'folder', 'folder_name',
            'unread_count', 'scrape_interval', 'scrape_interval_display',
            'last_scraped_at', 'is_healthy', 'is_subscribed', 'owner_email', 'created_at'
        ]
    
    def get_folder_name(self, obj):
        """Get folder name if haunt is in a folder"""
        return obj.folder.name if obj.folder else None
    
    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this haunt (vs owning it)"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # If user owns the haunt, they're not subscribed
        if obj.owner == request.user:
            return False
        
        # Use prefetched subscriptions if available to avoid N+1 queries
        if hasattr(obj, 'user_subscriptions_cache'):
            return len(obj.user_subscriptions_cache) > 0
        
        # Fallback to query if not prefetched (e.g., single object retrieval)
        from apps.subscriptions.models import Subscription
        return Subscription.objects.filter(user=request.user, haunt=obj).exists()
    
    def get_owner_email(self, obj):
        """Get owner email for subscribed haunts"""
        return obj.owner.email if obj.owner else None
    
    def get_unread_count(self, obj):
        """Get count of unread RSS items for this haunt"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        from apps.subscriptions.services import SubscriptionService
        return SubscriptionService.get_unread_count_for_haunt(request.user, obj)



class HauntCreateWithAISerializer(serializers.Serializer):
    """Serializer for creating haunts with AI-generated configuration"""

    url = serializers.URLField(required=True, help_text="URL to monitor")
    description = serializers.CharField(
        required=True,
        help_text="Natural language description of what to monitor"
    )
    name = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Display name for the haunt (auto-generated if not provided)"
    )
    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(),
        required=False,
        allow_null=True,
        help_text="Folder to organize this haunt"
    )
    scrape_interval = serializers.ChoiceField(
        choices=Haunt.SCRAPE_INTERVALS,
        default=60,
        help_text="How often to scrape (in minutes)"
    )
    enable_ai_summary = serializers.BooleanField(
        default=True,
        help_text="Enable AI-generated summaries and alert decisions"
    )

    def validate_folder(self, value):
        """Validate folder belongs to current user"""
        if value:
            request = self.context.get('request')
            if request and value.user != request.user:
                raise serializers.ValidationError(
                    "Folder must belong to the same user."
                )
        return value
