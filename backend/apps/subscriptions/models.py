from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Subscription(models.Model):
    """
    Model representing user subscriptions to public haunts.
    Allows users to follow haunts created by others.
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='subscriptions',
        help_text="User who subscribed to the haunt"
    )
    haunt = models.ForeignKey(
        'haunts.Haunt', 
        on_delete=models.CASCADE, 
        related_name='subscriptions',
        help_text="The haunt being subscribed to"
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the subscription was created"
    )
    
    # Subscription preferences
    notifications_enabled = models.BooleanField(
        default=True,
        help_text="Whether to receive notifications for this subscription"
    )
    
    class Meta:
        db_table = 'subscriptions_subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        unique_together = ['user', 'haunt']
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['user', '-subscribed_at']),
            models.Index(fields=['haunt']),
        ]
    
    def __str__(self):
        return f"{self.user.email} → {self.haunt.name}"
    
    def clean(self):
        """Validate subscription"""
        super().clean()
        
        # Ensure haunt is public
        if not self.haunt.is_public:
            raise ValidationError({
                'haunt': 'Can only subscribe to public haunts.'
            })
        
        # Prevent self-subscription
        if self.user == self.haunt.owner:
            raise ValidationError({
                'haunt': 'Cannot subscribe to your own haunt.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to validate before saving"""
        self.full_clean()
        super().save(*args, **kwargs)


class UserReadState(models.Model):
    """
    Model for tracking read/star state of RSS items per user.
    Allows users to mark items as read or starred across subscriptions.
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='read_states',
        help_text="User who owns this read state"
    )
    rss_item = models.ForeignKey(
        'rss.RSSItem', 
        on_delete=models.CASCADE, 
        related_name='read_states',
        help_text="The RSS item this state refers to"
    )
    
    # State flags
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the user has read this item"
    )
    is_starred = models.BooleanField(
        default=False,
        help_text="Whether the user has starred this item"
    )
    
    # Timestamps
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the item was marked as read"
    )
    starred_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the item was starred"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions_user_read_state'
        verbose_name = 'User Read State'
        verbose_name_plural = 'User Read States'
        unique_together = ['user', 'rss_item']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'is_starred']),
            models.Index(fields=['user', 'rss_item']),
            models.Index(fields=['rss_item']),
        ]
    
    def __str__(self):
        status = []
        if self.is_read:
            status.append('read')
        if self.is_starred:
            status.append('starred')
        status_str = ', '.join(status) if status else 'unread'
        return f"{self.user.email} - {self.rss_item.title[:50]} ({status_str})"
    
    def mark_read(self):
        """Mark item as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def mark_unread(self):
        """Mark item as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def toggle_starred(self):
        """Toggle starred state"""
        from django.utils import timezone
        self.is_starred = not self.is_starred
        self.starred_at = timezone.now() if self.is_starred else None
        self.save(update_fields=['is_starred', 'starred_at', 'updated_at'])
    
    @classmethod
    def get_or_create_for_user_item(cls, user, rss_item):
        """Get or create read state for user and RSS item"""
        read_state, created = cls.objects.get_or_create(
            user=user,
            rss_item=rss_item,
            defaults={
                'is_read': False,
                'is_starred': False,
            }
        )
        return read_state, created
    
    @classmethod
    def bulk_mark_read(cls, user, rss_items):
        """Bulk mark multiple items as read for a user"""
        from django.utils import timezone
        now = timezone.now()
        
        # Get existing read states
        existing_states = cls.objects.filter(
            user=user,
            rss_item__in=rss_items
        ).values_list('rss_item_id', flat=True)
        
        # Create read states for items that don't have them
        new_states = []
        update_states = []
        
        for item in rss_items:
            if item.id in existing_states:
                # Update existing unread states
                update_states.append(item.id)
            else:
                # Create new read states
                new_states.append(cls(
                    user=user,
                    rss_item=item,
                    is_read=True,
                    read_at=now
                ))
        
        # Bulk create new states
        if new_states:
            cls.objects.bulk_create(new_states)
        
        # Bulk update existing states
        if update_states:
            cls.objects.filter(
                user=user,
                rss_item_id__in=update_states,
                is_read=False
            ).update(is_read=True, read_at=now)