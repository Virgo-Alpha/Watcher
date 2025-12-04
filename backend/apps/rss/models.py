import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MaxLengthValidator

User = get_user_model()


class RSSItem(models.Model):
    """
    Model representing individual RSS feed items generated from haunt changes.
    Each item represents a detected change in a monitored site.
    """
    
    # Primary key and relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    haunt = models.ForeignKey(
        'haunts.Haunt', 
        on_delete=models.CASCADE, 
        related_name='rss_items',
        help_text="The haunt that generated this RSS item"
    )
    
    # RSS feed data
    title = models.CharField(
        max_length=300,
        help_text="RSS item title describing the change"
    )
    description = models.TextField(
        help_text="Detailed description of the change, may include AI summary"
    )
    link = models.URLField(
        help_text="Link to the monitored page"
    )
    guid = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for RSS item"
    )
    pub_date = models.DateTimeField(
        default=timezone.now,
        help_text="Publication date for RSS feed"
    )
    
    # Change data
    change_data = models.JSONField(
        default=dict,
        help_text="JSON data containing the detected changes"
    )
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated summary of the change"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rss_item'
        verbose_name = 'RSS Item'
        verbose_name_plural = 'RSS Items'
        ordering = ['-pub_date']
        indexes = [
            models.Index(fields=['haunt', '-pub_date']),
            models.Index(fields=['pub_date']),
            models.Index(fields=['guid']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.haunt.name})"
    
    def save(self, *args, **kwargs):
        """Override save to generate GUID if not provided"""
        if not self.guid:
            # Generate GUID from haunt ID and timestamp
            timestamp = self.pub_date.strftime('%Y%m%d%H%M%S')
            self.guid = f"{self.haunt.id}-{timestamp}"
        
        super().save(*args, **kwargs)
    
    @property
    def age_in_hours(self):
        """Get age of RSS item in hours"""
        return (timezone.now() - self.pub_date).total_seconds() / 3600
    
    @property
    def has_ai_summary(self):
        """Check if item has AI-generated summary"""
        return bool(self.ai_summary.strip())
    
    def get_change_summary(self):
        """Get a brief summary of changes"""
        if self.ai_summary:
            return self.ai_summary
        
        # Fallback to basic change description
        if self.change_data:
            changes = []
            for key, change in self.change_data.items():
                if isinstance(change, dict) and 'old' in change and 'new' in change:
                    changes.append(f"{key}: {change['old']} → {change['new']}")
            return '; '.join(changes) if changes else 'Changes detected'
        
        return 'Changes detected'