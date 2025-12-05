"""
Management command to populate demo RSS items with visible changes.
Creates realistic RSS items for demo haunts to showcase the UI.
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from apps.haunts.models import Haunt
from apps.rss.models import RSSItem

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate demo RSS items with visible changes for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='demo@watcher.local',
            help='Email for demo user (default: demo@watcher.local)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing RSS items before creating new ones',
        )

    def handle(self, *args, **options):
        email = options['email']
        clear = options['clear']
        
        try:
            demo_user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Demo user not found: {email}')
            )
            self.stdout.write('Run: python manage.py populate_demo_data first')
            return
        
        # Get demo user's haunts
        haunts = Haunt.objects.filter(owner=demo_user)
        
        if not haunts.exists():
            self.stdout.write(
                self.style.ERROR('No haunts found for demo user')
            )
            self.stdout.write('Run: python manage.py populate_demo_data first')
            return
        
        if clear:
            deleted_count = RSSItem.objects.filter(haunt__owner=demo_user).delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing RSS items')
            )
        
        # Define demo RSS items for each haunt type
        demo_items = {
            'GitHub Status': [
                {
                    'title': 'GitHub Status Changed',
                    'changes': {
                        'status': {'old': 'All Systems Operational', 'new': 'Minor Service Outage'},
                        'affected_services': {'old': 'None', 'new': 'Actions, Pages'}
                    },
                    'ai_summary': 'GitHub is experiencing a minor service outage affecting Actions and Pages. All other services remain operational.',
                    'hours_ago': 2
                },
                {
                    'title': 'GitHub Status Changed',
                    'changes': {
                        'status': {'old': 'Minor Service Outage', 'new': 'All Systems Operational'},
                        'affected_services': {'old': 'Actions, Pages', 'new': 'None'}
                    },
                    'ai_summary': 'GitHub services have been restored. All systems are now operational.',
                    'hours_ago': 1
                },
            ],
            'GPU Stock Tracker': [
                {
                    'title': 'RTX 4090 Stock Status Changed',
                    'changes': {
                        'availability': {'old': 'Out of Stock', 'new': 'In Stock'},
                        'price': {'old': '$1,599.99', 'new': '$1,599.99'}
                    },
                    'ai_summary': 'RTX 4090 is now in stock at Best Buy! Price remains at $1,599.99.',
                    'hours_ago': 3
                },
                {
                    'title': 'RTX 4090 Stock Status Changed',
                    'changes': {
                        'availability': {'old': 'In Stock', 'new': 'Out of Stock'},
                        'price': {'old': '$1,599.99', 'new': '$1,599.99'}
                    },
                    'ai_summary': 'RTX 4090 is now out of stock. It was available for approximately 45 minutes.',
                    'hours_ago': 2
                },
            ],
            'Hacker News Top Story': [
                {
                    'title': 'Top Story Changed',
                    'changes': {
                        'title': {'old': 'Show HN: I built a tool to monitor websites', 'new': 'GPT-5 Released by OpenAI'},
                        'points': {'old': '342', 'new': '1,247'},
                        'comments': {'old': '89', 'new': '423'}
                    },
                    'ai_summary': 'The top story on Hacker News changed to "GPT-5 Released by OpenAI" with 1,247 points and 423 comments.',
                    'hours_ago': 4
                },
                {
                    'title': 'Top Story Changed',
                    'changes': {
                        'title': {'old': 'GPT-5 Released by OpenAI', 'new': 'Show HN: Open source alternative to Vercel'},
                        'points': {'old': '1,247', 'new': '892'},
                        'comments': {'old': '423', 'new': '156'}
                    },
                    'ai_summary': 'New top story: "Show HN: Open source alternative to Vercel" with 892 points.',
                    'hours_ago': 1
                },
            ],
            'Course Registration Status': [
                {
                    'title': 'Registration Status Changed',
                    'changes': {
                        'status': {'old': 'Closed', 'new': 'Open'},
                        'available_seats': {'old': '0', 'new': '45'},
                        'deadline': {'old': 'N/A', 'new': 'January 15, 2025'}
                    },
                    'ai_summary': 'Course registration is now open! 45 seats available. Registration deadline is January 15, 2025.',
                    'hours_ago': 6
                },
            ],
            'Flight Price Monitor': [
                {
                    'title': 'Flight Price Changed',
                    'changes': {
                        'price': {'old': '$1,245', 'new': '$987'},
                        'airline': {'old': 'United', 'new': 'ANA'},
                        'stops': {'old': '1 stop', 'new': 'Nonstop'}
                    },
                    'ai_summary': 'Great deal! Nonstop flight to Tokyo dropped to $987 on ANA (was $1,245 with 1 stop on United).',
                    'hours_ago': 12
                },
                {
                    'title': 'Flight Price Changed',
                    'changes': {
                        'price': {'old': '$987', 'new': '$1,123'},
                        'airline': {'old': 'ANA', 'new': 'ANA'}
                    },
                    'ai_summary': 'Flight price increased to $1,123 (still a good deal compared to earlier prices).',
                    'hours_ago': 8
                },
            ],
            'Product Hunt #1': [
                {
                    'title': 'Top Product Changed',
                    'changes': {
                        'product_name': {'old': 'AI Code Assistant Pro', 'new': 'Watcher - Website Monitor'},
                        'votes': {'old': '1,234', 'new': '2,156'},
                        'maker': {'old': '@johndoe', 'new': '@watcherapp'}
                    },
                    'ai_summary': 'New #1 product: "Watcher - Website Monitor" by @watcherapp with 2,156 votes!',
                    'hours_ago': 5
                },
            ],
            'Apartment Listings': [
                {
                    'title': 'New Listing Found',
                    'changes': {
                        'new_listings': {'old': '3', 'new': '5'},
                        'lowest_price': {'old': '$2,100', 'new': '$1,950'},
                        'newest_address': {'old': '123 Main St', 'new': '456 Oak Ave'}
                    },
                    'ai_summary': '2 new apartments listed! Best deal: $1,950/mo at 456 Oak Ave (2BR, 1BA, downtown).',
                    'hours_ago': 18
                },
            ],
            'AWS Service Health': [
                {
                    'title': 'Service Status Changed',
                    'changes': {
                        'ec2_status': {'old': 'Operational', 'new': 'Service Disruption'},
                        'region': {'old': 'N/A', 'new': 'us-east-1'},
                        'impact': {'old': 'None', 'new': 'Elevated error rates'}
                    },
                    'ai_summary': 'AWS EC2 experiencing service disruption in us-east-1 with elevated error rates.',
                    'hours_ago': 24
                },
                {
                    'title': 'Service Status Changed',
                    'changes': {
                        'ec2_status': {'old': 'Service Disruption', 'new': 'Operational'},
                        'region': {'old': 'us-east-1', 'new': 'N/A'},
                        'impact': {'old': 'Elevated error rates', 'new': 'None'}
                    },
                    'ai_summary': 'AWS EC2 service has been restored in us-east-1. All systems operational.',
                    'hours_ago': 22
                },
            ],
        }
        
        created_count = 0
        now = timezone.now()
        
        with transaction.atomic():
            for haunt in haunts:
                if haunt.name in demo_items:
                    items_data = demo_items[haunt.name]
                    
                    for item_data in items_data:
                        pub_date = now - timedelta(hours=item_data['hours_ago'])
                        
                        # Create RSS item
                        rss_item = RSSItem.objects.create(
                            haunt=haunt,
                            title=item_data['title'],
                            description=self._format_description(item_data['changes']),
                            link=haunt.url,
                            guid=f"{haunt.id}-{pub_date.strftime('%Y%m%d%H%M%S')}",
                            pub_date=pub_date,
                            change_data=item_data['changes'],
                            ai_summary=item_data.get('ai_summary', '')
                        )
                        
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Created RSS item for {haunt.name}: {item_data["title"]}'
                            )
                        )
                    
                    # Update haunt's current state to reflect latest change
                    latest_item = items_data[0]  # Most recent
                    current_state = {
                        key: change['new']
                        for key, change in latest_item['changes'].items()
                    }
                    haunt.current_state = current_state
                    haunt.last_scraped_at = now - timedelta(hours=latest_item['hours_ago'])
                    haunt.save(update_fields=['current_state', 'last_scraped_at'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Created {created_count} demo RSS items across {len(demo_items)} haunts'
            )
        )
    
    def _format_description(self, changes):
        """Format changes into a readable description"""
        lines = []
        for key, change in changes.items():
            old_val = change['old']
            new_val = change['new']
            lines.append(f"{key}: {old_val} → {new_val}")
        return '\n'.join(lines)
