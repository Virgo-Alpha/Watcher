from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import RSSItem


@admin.register(RSSItem)
class RSSItemAdmin(admin.ModelAdmin):
    """Admin configuration for RSSItem model"""
    
    list_display = (
        'title_short', 'haunt_name', 'haunt_owner', 'pub_date', 
        'has_ai_summary', 'age_display', 'created_at'
    )
    list_filter = (
        'pub_date', 'created_at', 'haunt__is_public', 
        'haunt__owner', 'haunt__alert_mode'
    )
    search_fields = (
        'title', 'description', 'ai_summary', 'haunt__name', 
        'haunt__owner__email', 'haunt__owner__username'
    )
    readonly_fields = (
        'id', 'guid', 'created_at', 'age_display', 'change_summary'
    )
    ordering = ('-pub_date',)
    date_hierarchy = 'pub_date'
    
    fieldsets = (
        ('RSS Item Information', {
            'fields': ('id', 'haunt', 'title', 'description', 'link', 'guid')
        }),
        ('Change Data', {
            'fields': ('change_data', 'ai_summary', 'change_summary')
        }),
        ('Timestamps', {
            'fields': ('pub_date', 'created_at', 'age_display'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        """Display shortened title"""
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Title'
    
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
    haunt_owner.short_description = 'Owner'
    
    def has_ai_summary(self, obj):
        """Display AI summary status"""
        if obj.has_ai_summary:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_ai_summary.short_description = 'AI Summary'
    has_ai_summary.boolean = True
    
    def age_display(self, obj):
        """Display age of RSS item"""
        hours = obj.age_in_hours
        if hours < 1:
            return f"{int(hours * 60)} minutes ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        else:
            return f"{int(hours / 24)} days ago"
    age_display.short_description = 'Age'
    
    def change_summary(self, obj):
        """Display change summary"""
        return obj.get_change_summary()
    change_summary.short_description = 'Change Summary'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('haunt', 'haunt__owner')
    
    actions = ['delete_old_items']
    
    def delete_old_items(self, request, queryset):
        """Admin action to delete old RSS items"""
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        old_items = queryset.filter(pub_date__lt=cutoff_date)
        count = old_items.count()
        old_items.delete()
        self.message_user(request, f'Deleted {count} RSS items older than 30 days.')
    delete_old_items.short_description = 'Delete items older than 30 days'