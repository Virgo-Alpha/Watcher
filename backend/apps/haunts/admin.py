from django.contrib import admin
from django.utils.html import format_html
from .models import Haunt, Folder, UserUIPreferences


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    """Admin configuration for Folder model"""
    
    list_display = ('name', 'user', 'parent', 'full_path', 'haunt_count', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('user', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'parent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_path(self, obj):
        """Display full folder path"""
        return obj.get_full_path()
    full_path.short_description = 'Full Path'
    
    def haunt_count(self, obj):
        """Display number of haunts in folder"""
        return obj.haunts.count()
    haunt_count.short_description = 'Haunts'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user', 'parent').prefetch_related('haunts')


@admin.register(UserUIPreferences)
class UserUIPreferencesAdmin(admin.ModelAdmin):
    """Admin configuration for UserUIPreferences model"""
    
    list_display = (
        'user', 'left_panel_width', 'middle_panel_width', 
        'keyboard_shortcuts_enabled', 'auto_mark_read_on_scroll', 'updated_at'
    )
    list_filter = (
        'keyboard_shortcuts_enabled', 'auto_mark_read_on_scroll', 
        'auto_mark_read_on_open', 'show_read_items'
    )
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('user',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Panel Widths', {
            'fields': ('left_panel_width', 'middle_panel_width')
        }),
        ('Behavior Settings', {
            'fields': (
                'keyboard_shortcuts_enabled', 'auto_mark_read_on_scroll', 
                'auto_mark_read_on_open', 'show_read_items'
            )
        }),
        ('Display Settings', {
            'fields': ('items_per_page', 'collapsed_folders')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Haunt)
class HauntAdmin(admin.ModelAdmin):
    """Admin configuration for Haunt model"""
    
    list_display = (
        'name', 'owner', 'folder', 'url_link', 'is_active', 'is_public', 
        'scrape_interval_display', 'alert_mode', 'is_healthy_display', 'created_at'
    )
    list_filter = (
        'is_active', 'is_public', 'alert_mode', 'scrape_interval', 
        'created_at', 'last_scraped_at'
    )
    search_fields = ('name', 'url', 'description', 'owner__email', 'owner__username')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'last_scraped_at', 
        'error_count', 'last_error', 'public_slug'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'owner', 'folder', 'name', 'url', 'description')
        }),
        ('Configuration', {
            'fields': ('config', 'scrape_interval', 'alert_mode')
        }),
        ('State', {
            'fields': ('current_state', 'last_alert_state', 'is_active')
        }),
        ('Public Sharing', {
            'fields': ('is_public', 'public_slug'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('last_scraped_at', 'error_count', 'last_error'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def url_link(self, obj):
        """Display URL as clickable link"""
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:50])
    url_link.short_description = 'URL'
    
    def is_healthy_display(self, obj):
        """Display health status with color coding"""
        if obj.is_healthy:
            return format_html('<span style="color: green;">✓ Healthy</span>')
        else:
            return format_html('<span style="color: red;">✗ Unhealthy ({})</span>', obj.error_count)
    is_healthy_display.short_description = 'Health'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('owner', 'folder')
    
    actions = ['make_active', 'make_inactive', 'reset_errors']
    
    def make_active(self, request, queryset):
        """Admin action to activate haunts"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} haunts were activated.')
    make_active.short_description = 'Activate selected haunts'
    
    def make_inactive(self, request, queryset):
        """Admin action to deactivate haunts"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} haunts were deactivated.')
    make_inactive.short_description = 'Deactivate selected haunts'
    
    def reset_errors(self, request, queryset):
        """Admin action to reset error counts"""
        for haunt in queryset:
            haunt.reset_error_count()
        self.message_user(request, f'Error counts reset for {queryset.count()} haunts.')
    reset_errors.short_description = 'Reset error counts'