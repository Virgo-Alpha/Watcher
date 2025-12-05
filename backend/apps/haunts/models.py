import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError

User = get_user_model()


class Folder(models.Model):
    """
    Model for organizing haunts into folders.
    Supports hierarchical folder structure.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=100, help_text="Folder name")
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='children',
        help_text="Parent folder for hierarchical organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'haunts_folder'
        verbose_name = 'Folder'
        verbose_name_plural = 'Folders'
        unique_together = ['user', 'name', 'parent']
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'parent']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name}/{self.name}"
        return self.name
    
    def clean(self):
        """Validate folder hierarchy"""
        super().clean()
        
        # Prevent circular references
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError({
                        'parent': 'Folder cannot be its own parent or ancestor.'
                    })
                current = current.parent
    
    def get_full_path(self):
        """Get full path of folder including parents"""
        path_parts = [self.name]
        current = self.parent
        while current:
            path_parts.insert(0, current.name)
            current = current.parent
        return '/'.join(path_parts)
    
    def get_descendants(self):
        """Get all descendant folders using iterative approach to avoid N+1 queries"""
        descendants = []
        to_process = list(self.children.select_related('parent').all())
        processed_ids = {self.id}

        while to_process:
            current = to_process.pop(0)
            if current.id in processed_ids:
                continue
            processed_ids.add(current.id)
            descendants.append(current)

            # Fetch children for current folder
            children = list(Folder.objects.filter(parent=current).select_related('parent'))
            to_process.extend(children)

        return descendants
    
    @property
    def depth(self):
        """Get folder depth in hierarchy"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth


class UserUIPreferences(models.Model):
    """
    Model for storing user UI preferences and settings.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ui_preferences')
    
    # Panel width preferences (in pixels)
    left_panel_width = models.IntegerField(
        default=250,
        validators=[MinValueValidator(200), MaxValueValidator(500)],
        help_text="Width of the navigation panel in pixels"
    )
    middle_panel_width = models.IntegerField(
        default=400,
        validators=[MinValueValidator(300), MaxValueValidator(800)],
        help_text="Width of the item list panel in pixels"
    )
    
    # UI behavior preferences
    keyboard_shortcuts_enabled = models.BooleanField(
        default=True,
        help_text="Enable keyboard shortcuts (J/K navigation, etc.)"
    )
    auto_mark_read_on_scroll = models.BooleanField(
        default=False,
        help_text="Automatically mark items as read when scrolled past"
    )
    auto_mark_read_on_open = models.BooleanField(
        default=True,
        help_text="Automatically mark items as read when opened"
    )
    
    # Folder state preferences
    collapsed_folders = models.JSONField(
        default=list,
        help_text="List of folder IDs that are collapsed in the UI"
    )
    
    # Display preferences
    items_per_page = models.IntegerField(
        default=50,
        validators=[MinValueValidator(10), MaxValueValidator(200)],
        help_text="Number of items to display per page"
    )
    show_read_items = models.BooleanField(
        default=True,
        help_text="Show read items in the item list"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'haunts_user_ui_preferences'
        verbose_name = 'User UI Preferences'
        verbose_name_plural = 'User UI Preferences'
    
    def __str__(self):
        return f"UI Preferences for {self.user.email}"
    
    def is_folder_collapsed(self, folder_id):
        """Check if a folder is collapsed (optimized with set for O(1) lookup)"""
        collapsed_set = set(self.collapsed_folders)
        return str(folder_id) in collapsed_set
    
    def toggle_folder_collapsed(self, folder_id):
        """Toggle folder collapsed state"""
        folder_id_str = str(folder_id)
        collapsed_list = list(self.collapsed_folders)  # Create mutable copy
        if folder_id_str in collapsed_list:
            collapsed_list.remove(folder_id_str)
        else:
            collapsed_list.append(folder_id_str)
        self.collapsed_folders = collapsed_list
        self.save(update_fields=['collapsed_folders'])


class Haunt(models.Model):
    """
    Model representing a monitored website (haunt).
    Tracks configuration, state, and metadata for site monitoring.
    """
    
    # Scrape interval choices (in minutes)
    SCRAPE_INTERVALS = [
        (15, '15 minutes'),
        (30, '30 minutes'),
        (60, '1 hour'),
        (1440, '24 hours'),  # 24 * 60 = 1440 minutes
    ]
    
    # Primary key and ownership
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='haunts')
    folder = models.ForeignKey(
        Folder, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='haunts',
        help_text="Folder containing this haunt"
    )
    
    # Basic haunt information
    name = models.CharField(max_length=200, help_text="Display name for the haunt")
    url = models.URLField(help_text="URL to monitor")
    description = models.TextField(
        blank=True, 
        help_text="Natural language description of what to monitor"
    )
    
    # Configuration and state
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON configuration with selectors, normalization rules, and truthy values"
    )
    current_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="Current key-value state extracted from the site"
    )
    last_alert_state = models.JSONField(
        null=True, 
        blank=True,
        help_text="State when last alert was sent (for 'once' alert mode)"
    )
    
    # Monitoring configuration
    scrape_interval = models.IntegerField(
        choices=SCRAPE_INTERVALS,
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(1440)],
        help_text="How often to scrape the site (in minutes)"
    )
    enable_ai_summary = models.BooleanField(
        default=True,
        help_text="Enable AI-generated summaries and alert decisions"
    )
    
    # Public sharing
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this haunt is publicly visible"
    )
    public_slug = models.SlugField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="URL-friendly identifier for public access"
    )
    
    # Status tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether monitoring is active"
    )
    last_scraped_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this haunt was last scraped"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message if scraping failed"
    )
    error_count = models.IntegerField(
        default=0,
        help_text="Consecutive error count"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'haunts_haunt'
        verbose_name = 'Haunt'
        verbose_name_plural = 'Haunts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['owner', 'folder']),
            models.Index(fields=['is_public', 'public_slug']),
            models.Index(fields=['scrape_interval', 'is_active']),
            models.Index(fields=['last_scraped_at']),
            models.Index(fields=['-created_at']),  # For list ordering
        ]
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def clean(self):
        """Validate model fields"""
        super().clean()
        
        # Validate scrape interval
        if self.scrape_interval not in [choice[0] for choice in self.SCRAPE_INTERVALS]:
            raise ValidationError({
                'scrape_interval': 'Invalid scrape interval. Must be 15, 30, 60, or 1440 minutes.'
            })
        
        # Validate folder ownership
        if self.folder and self.folder.user != self.owner:
            raise ValidationError({
                'folder': 'Folder must belong to the same user as the haunt.'
            })
        
        # Validate config structure if provided
        if self.config and self.config != {}:
            required_keys = ['selectors', 'normalization']
            for key in required_keys:
                if key not in self.config:
                    raise ValidationError({
                        'config': f'Configuration must include "{key}" key.'
                    })
    
    def save(self, *args, **kwargs):
        """Override save to handle public slug generation"""
        # Generate public slug if making public and no slug exists
        if self.is_public and not self.public_slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Ensure unique slug
            while Haunt.objects.filter(public_slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.public_slug = slug
        
        # Clear public slug if making private
        elif not self.is_public:
            self.public_slug = None
        
        # Validate before saving
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    @property
    def is_healthy(self):
        """Check if haunt is healthy (low error count)"""
        return self.error_count < 5
    
    @property
    def scrape_interval_display(self):
        """Get human-readable scrape interval"""
        return dict(self.SCRAPE_INTERVALS).get(self.scrape_interval, 'Unknown')
    
    def reset_error_count(self):
        """Reset error count after successful scrape"""
        self.error_count = 0
        self.last_error = ''
        self.save(update_fields=['error_count', 'last_error'])
    
    def increment_error_count(self, error_message=''):
        """Increment error count and store error message"""
        self.error_count += 1
        self.last_error = error_message
        self.save(update_fields=['error_count', 'last_error'])
    
    def get_public_url(self):
        """Get public URL for this haunt if it's public"""
        if self.is_public and self.public_slug:
            return f"/public/haunts/{self.public_slug}/"
        return None
    
    def get_rss_url(self, request=None):
        """Get RSS feed URL for this haunt"""
        if self.is_public and self.public_slug:
            return f"/rss/public/{self.public_slug}/"
        else:
            return f"/rss/private/{self.id}/"