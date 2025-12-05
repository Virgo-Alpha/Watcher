"""
Management command to fix broken haunt selectors with working configurations.
Updates existing haunts with proper CSS selectors that match actual DOM structures.
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.haunts.models import Haunt

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix broken haunt selectors with working configurations based on actual site structures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Define working configurations for each problematic haunt
        haunt_configs = {
            'GitHub Status': {
                'description': 'Monitor GitHub service status - is everything operational?',
                'config': {
                    'selectors': {
                        'status': 'css:.color-text-primary',
                        'incidents': 'css:.unresolved-incidents',
                    },
                    'normalization': {
                        'status': {
                            'type': 'text',
                            'transform': 'lowercase',
                            'strip': True
                        },
                        'incidents': {
                            'type': 'text',
                            'strip': True
                        }
                    },
                    'truthy_values': {
                        'status': ['all systems operational', 'operational'],
                        'incidents': ['no incidents']
                    }
                }
            },
            
            'AWS Service Health': {
                'description': 'Monitor AWS service health for any outages',
                'config': {
                    'selectors': {
                        'overall_status': 'css:[data-testid="service-health-status"]',
                        'service_issues': 'css:.service-health-issue',
                    },
                    'normalization': {
                        'overall_status': {
                            'type': 'text',
                            'transform': 'lowercase',
                            'strip': True
                        },
                        'service_issues': {
                            'type': 'text',
                            'strip': True
              