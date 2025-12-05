"""
RSS service business logic for creating and managing RSS items.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from django.utils import timezone
from django.utils.html import escape
from django.core.cache import cache
from django.db.models import Prefetch

from apps.rss.models import RSSItem
from apps.haunts.models import Haunt

logger = logging.getLogger(__name__)

# Cache timeout in seconds (15 minutes)
RSS_CACHE_TIMEOUT = 900


class RSSService:
    """
    Service for creating and managing RSS items from haunt changes.
    """

    def create_rss_item(
        self,
        haunt: Haunt,
        changes: Dict[str, Any],
        ai_summary: Optional[str] = None
    ) -> RSSItem:
        """
        Create an RSS item for detected changes.

        Args:
            haunt: Haunt that generated the change
            changes: Dictionary of changes with old and new values
            ai_summary: Optional AI-generated summary

        Returns:
            Created RSSItem instance
        """
        # Generate title from changes
        title = self._generate_title(haunt, changes)

        # Generate description from changes
        description = self._generate_description(changes, ai_summary)

        # Create RSS item
        rss_item = RSSItem.objects.create(
            haunt=haunt,
            title=title,
            description=description,
            link=haunt.url,
            pub_date=timezone.now(),
            change_data=changes,
            ai_summary=ai_summary or ''
        )

        logger.info('Created RSS item %s for haunt %s', rss_item.id, haunt.id)

        # Invalidate cache for this haunt
        self.invalidate_feed_cache(haunt)

        return rss_item

    def _generate_title(self, haunt: Haunt, changes: Dict[str, Any]) -> str:
        """
        Generate RSS item title from changes.
        
        Args:
            haunt: Haunt that generated the change
            changes: Dictionary of changes
        
        Returns:
            Title string
        """
        if not changes:
            return f"{haunt.name}: Changes detected"
        
        # Get first change for title
        first_key = list(changes.keys())[0]
        first_change = changes[first_key]
        
        if isinstance(first_change, dict) and 'old' in first_change and 'new' in first_change:
            old_val = first_change.get('old', 'None')
            new_val = first_change.get('new', 'None')
            
            # Truncate long values
            old_val_str = str(old_val)[:50]
            new_val_str = str(new_val)[:50]
            
            if len(changes) == 1:
                return f"{haunt.name}: {first_key} changed to {new_val_str}"
            else:
                return f"{haunt.name}: {first_key} changed (and {len(changes) - 1} more)"
        
        return f"{haunt.name}: Changes detected"

    def _generate_description(
        self,
        changes: Dict[str, Any],
        ai_summary: Optional[str] = None
    ) -> str:
        """
        Generate RSS item description from changes.
        
        Args:
            changes: Dictionary of changes
            ai_summary: Optional AI-generated summary
        
        Returns:
            Description string
        """
        if ai_summary:
            return ai_summary
        
        # Generate description from changes
        if not changes:
            return "Changes detected"
        
        change_lines = []
        for key, change in changes.items():
            if isinstance(change, dict) and 'old' in change and 'new' in change:
                old_val = change.get('old', 'None')
                new_val = change.get('new', 'None')
                change_lines.append(f"{key}: {old_val} → {new_val}")
        
        if change_lines:
            return "\n".join(change_lines)
        
        return "Changes detected"

    def get_recent_items(self, haunt: Haunt, limit: int = 50) -> list:
        """
        Get recent RSS items for a haunt with optimized query.

        Args:
            haunt: Haunt to get items for
            limit: Maximum number of items to return

        Returns:
            List of RSSItem instances
        """
        return list(
            RSSItem.objects.filter(haunt=haunt)
            .select_related('haunt')
            .only('id', 'title', 'description', 'link', 'pub_date', 'guid', 'ai_summary', 'haunt__name', 'haunt__url')
            .order_by('-pub_date')[:limit]
        )

    def get_unread_count(self, haunt: Haunt, user) -> int:
        """
        Get count of unread items for a haunt and user.

        Args:
            haunt: Haunt to count items for
            user: User to check read state for

        Returns:
            Count of unread items
        """
        from apps.subscriptions.models import UserReadState

        # Get all RSS items for haunt
        all_items = RSSItem.objects.filter(haunt=haunt).values_list('id', flat=True)

        # Get read items for user
        read_items = UserReadState.objects.filter(
            user=user,
            rss_item_id__in=all_items,
            is_read=True
        ).values_list('rss_item_id', flat=True)

        # Calculate unread count
        return len(all_items) - len(read_items)

    def generate_rss_feed(self, haunt: Haunt, limit: int = 50, use_cache: bool = True) -> str:
        """
        Generate RSS 2.0 XML feed for a haunt with caching.

        Args:
            haunt: Haunt to generate feed for
            limit: Maximum number of items to include
            use_cache: Whether to use cached feed if available

        Returns:
            RSS XML string
        """
        # Try to get from cache
        if use_cache:
            cache_key = self._get_cache_key(haunt)
            cached_feed = cache.get(cache_key)
            if cached_feed:
                logger.debug('Returning cached RSS feed for haunt %s', haunt.id)
                return cached_feed

        # Get recent RSS items with optimized query
        items = self.get_recent_items(haunt, limit)

        # Create RSS root element
        rss = Element('rss', version='2.0')

        # Create channel element
        channel = SubElement(rss, 'channel')

        # Add channel metadata
        title = SubElement(channel, 'title')
        title.text = escape(haunt.name)

        link = SubElement(channel, 'link')
        link.text = escape(haunt.url)

        description = SubElement(channel, 'description')
        description.text = escape(haunt.description or f"Change monitoring for {haunt.name}")

        # Add last build date
        last_build_date = SubElement(channel, 'lastBuildDate')
        last_build_date.text = self._format_rfc822_date(timezone.now())

        # Add generator
        generator = SubElement(channel, 'generator')
        generator.text = 'Watcher - Site Change Monitor'

        # Add items
        for rss_item in items:
            self._add_rss_item_element(channel, rss_item)

        # Convert to pretty-printed XML string
        xml_string = tostring(rss, encoding='unicode')
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent='  ')

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        feed_xml = '\n'.join(lines)

        # Cache the feed
        if use_cache:
            cache_key = self._get_cache_key(haunt)
            cache.set(cache_key, feed_xml, RSS_CACHE_TIMEOUT)
            logger.debug('Cached RSS feed for haunt %s', haunt.id)

        return feed_xml

    def _add_rss_item_element(self, channel: Element, rss_item: RSSItem) -> None:
        """
        Add an RSS item element to the channel.

        Args:
            channel: Channel element to add item to
            rss_item: RSSItem instance to convert to XML
        """
        item = SubElement(channel, 'item')

        # Add title
        title = SubElement(item, 'title')
        title.text = escape(rss_item.title)

        # Add link
        link = SubElement(item, 'link')
        link.text = escape(rss_item.link)

        # Add description (with AI summary if available)
        description = SubElement(item, 'description')
        if rss_item.ai_summary:
            # Include AI summary prominently
            desc_text = f"<p><strong>Summary:</strong> {escape(rss_item.ai_summary)}</p>"
            desc_text += f"<p><strong>Changes:</strong></p><pre>{escape(rss_item.description)}</pre>"
            description.text = desc_text
        else:
            description.text = escape(rss_item.description)

        # Add publication date
        pub_date = SubElement(item, 'pubDate')
        pub_date.text = self._format_rfc822_date(rss_item.pub_date)

        # Add GUID
        guid = SubElement(item, 'guid', isPermaLink='false')
        guid.text = escape(rss_item.guid)

    def _format_rfc822_date(self, dt: datetime) -> str:
        """
        Format datetime as RFC 822 date string for RSS.

        Args:
            dt: Datetime to format

        Returns:
            RFC 822 formatted date string
        """
        # Ensure datetime is timezone-aware
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)

        # Format as RFC 822 (e.g., "Mon, 01 Jan 2024 12:00:00 +0000")
        return dt.strftime('%a, %d %b %Y %H:%M:%S %z')

    def _get_cache_key(self, haunt: Haunt) -> str:
        """
        Get cache key for a haunt's RSS feed.

        Args:
            haunt: Haunt to get cache key for

        Returns:
            Cache key string
        """
        return f'rss_feed:{haunt.id}'

    def invalidate_feed_cache(self, haunt: Haunt) -> None:
        """
        Invalidate cached RSS feed for a haunt.

        Args:
            haunt: Haunt to invalidate cache for
        """
        cache_key = self._get_cache_key(haunt)
        cache.delete(cache_key)
        logger.debug('Invalidated RSS feed cache for haunt %s', haunt.id)



class EmailNotificationService:
    """
    Service for sending email notifications about haunt changes.
    """
    
    @staticmethod
    def get_notification_recipients(haunt: Haunt) -> list:
        """
        Get list of users who should receive notifications for this haunt.
        
        Args:
            haunt: The haunt that changed
            
        Returns:
            List of User objects who should be notified
        """
        from django.contrib.auth import get_user_model
        from apps.subscriptions.models import Subscription
        
        User = get_user_model()
        recipients = []
        
        # Add haunt owner if they have notifications enabled
        if haunt.owner.email_notifications_enabled:
            recipients.append(haunt.owner)
            logger.debug(f'Added owner {haunt.owner.email} to recipients')
        
        # Add subscribers who have notifications enabled
        if haunt.is_public:
            subscriptions = Subscription.objects.filter(
                haunt=haunt,
                notifications_enabled=True,
                user__email_notifications_enabled=True
            ).select_related('user')
            
            for subscription in subscriptions:
                if subscription.user != haunt.owner:  # Don't duplicate owner
                    recipients.append(subscription.user)
                    logger.debug(f'Added subscriber {subscription.user.email} to recipients')
        
        logger.info(f'Found {len(recipients)} recipients for haunt {haunt.id}')
        return recipients
    
    @staticmethod
    def send_change_notification(rss_item: RSSItem) -> dict:
        """
        Send email notification about a haunt change.
        
        Args:
            rss_item: The RSS item representing the change
            
        Returns:
            dict with 'sent' count and 'failed' count
        """
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        
        haunt = rss_item.haunt
        recipients = EmailNotificationService.get_notification_recipients(haunt)
        
        if not recipients:
            logger.info(f'No recipients for haunt {haunt.id}, skipping email')
            return {'sent': 0, 'failed': 0}
        
        # Prepare email content
        subject = f'[Watcher] {haunt.name} - Change Detected'
        
        # Plain text version
        text_content = EmailNotificationService._render_text_email(rss_item)
        
        # HTML version
        html_content = EmailNotificationService._render_html_email(rss_item)
        
        # Send emails
        sent_count = 0
        failed_count = 0
        
        for user in recipients:
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@watcher.local',
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                sent_count += 1
                logger.info(f'Sent notification to {user.email} for haunt {haunt.id}')
                
            except Exception as e:
                failed_count += 1
                logger.error(f'Failed to send notification to {user.email}: {e}')
        
        logger.info(f'Email notification complete: {sent_count} sent, {failed_count} failed')
        return {'sent': sent_count, 'failed': failed_count}
    
    @staticmethod
    def _render_text_email(rss_item: RSSItem) -> str:
        """
        Render plain text email content.
        
        Args:
            rss_item: The RSS item to render
            
        Returns:
            Plain text email content
        """
        haunt = rss_item.haunt
        
        lines = [
            f'Change detected in: {haunt.name}',
            f'URL: {haunt.url}',
            '',
            f'Title: {rss_item.title}',
            '',
        ]
        
        # Add summary if available
        if rss_item.ai_summary:
            lines.append('Summary:')
            lines.append(rss_item.ai_summary)
            lines.append('')
        
        # Add changes
        if rss_item.change_data:
            lines.append('Changes:')
            for field, change in rss_item.change_data.items():
                if isinstance(change, dict) and 'old' in change and 'new' in change:
                    lines.append(f'  • {field}:')
                    lines.append(f'    Old: {change["old"]}')
                    lines.append(f'    New: {change["new"]}')
                else:
                    lines.append(f'  • {field}: {change}')
            lines.append('')
        
        lines.append('---')
        lines.append('View in Watcher: [Link to your Watcher instance]')
        lines.append('')
        lines.append('To disable these notifications, update your settings in Watcher.')
        
        return '\n'.join(lines)
    
    @staticmethod
    def _render_html_email(rss_item: RSSItem) -> str:
        """
        Render HTML email content.
        
        Args:
            rss_item: The RSS item to render
            
        Returns:
            HTML email content
        """
        haunt = rss_item.haunt
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    color: #333333;
                    line-height: 1.6;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #FAFAFA;
                    border-left: 4px solid #DD4B39;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                .haunt-name {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #333333;
                    margin: 0 0 5px 0;
                }}
                .haunt-url {{
                    font-size: 13px;
                    color: #777777;
                    margin: 0;
                }}
                .content {{
                    padding: 15px 0;
                }}
                .title {{
                    font-size: 16px;
                    font-weight: bold;
                    color: #3366CC;
                    margin: 0 0 15px 0;
                }}
                .summary {{
                    background-color: #F5F5F5;
                    padding: 12px;
                    border-radius: 4px;
                    margin: 15px 0;
                    font-size: 14px;
                }}
                .changes {{
                    margin: 15px 0;
                }}
                .change-item {{
                    margin: 10px 0;
                    padding: 10px;
                    background-color: #FAFAFA;
                    border-left: 3px solid #E5E5E5;
                }}
                .change-field {{
                    font-weight: bold;
                    color: #333333;
                }}
                .change-value {{
                    color: #777777;
                    font-size: 13px;
                    margin: 3px 0;
                }}
                .old-value {{
                    text-decoration: line-through;
                    color: #999999;
                }}
                .new-value {{
                    color: #DD4B39;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #E5E5E5;
                    font-size: 12px;
                    color: #777777;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <p class="haunt-name">{haunt.name}</p>
                <p class="haunt-url">{haunt.url}</p>
            </div>
            
            <div class="content">
                <p class="title">{rss_item.title}</p>
        '''
        
        # Add summary if available
        if rss_item.ai_summary:
            html += f'''
                <div class="summary">
                    {rss_item.ai_summary}
                </div>
            '''
        
        # Add changes
        if rss_item.change_data:
            html += '<div class="changes"><strong>Changes:</strong>'
            for field, change in rss_item.change_data.items():
                html += f'<div class="change-item">'
                html += f'<div class="change-field">{field}</div>'
                
                if isinstance(change, dict) and 'old' in change and 'new' in change:
                    html += f'<div class="change-value old-value">Old: {change["old"]}</div>'
                    html += f'<div class="change-value new-value">New: {change["new"]}</div>'
                else:
                    html += f'<div class="change-value">{change}</div>'
                
                html += '</div>'
            html += '</div>'
        
        html += '''
            </div>
            
            <div class="footer">
                <p>To disable these notifications, update your settings in Watcher.</p>
            </div>
        </body>
        </html>
        '''
        
        return html
