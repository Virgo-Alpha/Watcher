from django.contrib import admin
from django.utils.html import format_html
from .models import Subscription, UserReadState


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for Subscription model"""
    
    list_display = (
        'user_email', 'haunt_name', 'haunt_owner', 'notifications_enabled', 
        'subscribed_at', 'haunt_is_active'
    )
    list_filter = (
        'notifications_enabled', 'subscribed_at', 'haunt__is_active', 
        'haunt__is_public'
    )
    search_fields = (
        'user__email', 'user__username', 'haunt__name', 
        'haunt__owner__email', 'haunt__owner__username'
    )
    readonly_fields = ('subscribed_at',)
    ordering = ('-subscribed_at',)
    date_hierarchy = 'subscribed_at'
    
    fieldsets = (
        ('Subscription', {
            'fields': ('user', 'haunt', 'notifications_enabled')
        }),
        ('Timestamps', {
            'fields': ('subscribed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    
    def haunt_name(self, obj):
        """Display haunt name with link"""
        return format_html(
            '<a href="/admin/haunts/haunt/{}/change/">{}</a>',
            obj.haunt.id, obj.haunt.name
        )
    haunt_name.short_description = 'Haunt'
    
    def haunt_owner(self, obj):
        """Display haunt owner"""
        return obj.haunt.owner.email
    haunt_owner.short_description = 'Haunt Owner'
    
    def haunt_is_active(self, obj):
        """Display haunt active status"""
        if obj.haunt.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    haunt_is_active.short_description = 'Haunt Status'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user', 'haunt', 'haunt__owner')
    
    actions = ['enable_notifications', 'disable_notifications']
    
    def enable_notifications(self, request, queryset):
        """Enable notifications for selected subscriptions"""
        updated = queryset.update(notifications_enabled=True)
        self.message_user(request, f'Enabled notifications for {updated} subscriptions.')
    enable_notifications.short_description = 'Enable notifications'
    
    def disable_notifications(self, request, queryset):
        """Disable notifications for selected subscriptions"""
        updated = queryset.update(notifications_enabled=False)
        self.message_user(request, f'Disabled notifications for {updated} subscriptions.')
    disable_notifications.short_description = 'Disable notifications'


@admin.register(UserReadState)
class UserReadStateAdmin(admin.ModelAdmin):
    """Admin configuration for UserReadState model"""
    
    list_display = (
        'user_email', 'rss_item_title', 'haunt_name', 'is_read', 
        'is_starred', 'read_at', 'starred_at', 'updated_at'
    )
    list_filter = (
        'is_read', 'is_starred', 'read_at', 'starred_at', 
        'created_at', 'rss_item__haunt__owner'
    )
    search_fields = (
        'user__email', 'user__username', 'rss_item__title', 
        'rss_item__haunt__name', 'rss_item__haunt__owner__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)
    date_hierarchy = 'updated_at'
    
    fieldsets = (
        ('Read State', {
            'fields': ('user', 'rss_item', 'is_read', 'is_starred')
        }),
        ('Timestamps', {
            'fields': ('read_at', 'starred_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    
    def rss_item_title(self, obj):
        """Display RSS item title (shortened)"""
        title = obj.rss_item.title
        return title[:50] + '...' if len(title) > 50 else title
    rss_item_title.short_description = 'RSS Item'
    
    def haunt_name(self, obj):
        """Display haunt name"""
        return obj.rss_item.haunt.name
    haunt_name.short_description = 'Haunt'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'user', 'rss_item', 'rss_item__haunt', 'rss_item__haunt__owner'
        )
    
    actions = ['mark_read', 'mark_unread', 'toggle_starred']
    
    def mark_read(self, request, queryset):
        """Mark selected items as read"""
        for read_state in queryset:
            read_state.mark_read()
        self.message_user(request, f'Marked {queryset.count()} items as read.')
    mark_read.short_description = 'Mark as read'
    
    def mark_unread(self, request, queryset):
        """Mark selected items as unread"""
        for read_state in queryset:
            read_state.mark_unread()
        self.message_user(request, f'Marked {queryset.count()} items as unread.')
    mark_unread.short_description = 'Mark as unread'
    
    def toggle_starred(self, request, queryset):
        """Toggle starred status for selected items"""
        for read_state in queryset:
            read_state.toggle_starred()
        self.message_user(request, f'Toggled starred status for {queryset.count()} items.')
    toggle_starred.short_description = 'Toggle starred'