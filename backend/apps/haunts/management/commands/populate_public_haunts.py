"""
Management command to populate public haunts that are available to all users.
These haunts serve as examples and useful monitoring configurations.
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.haunts.models import Haunt
from apps.ai.services import AIConfigService

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate database with public haunts available to all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Delete existing public haunts and recreate them',
        )

    def handle(self, *args, **options):
        recreate = options['recreate']
        
        # Get or create system user for public haunts
        system_user, created = User.objects.get_or_create(
            email='system@watcher.local',
            defaults={
                'username': 'system',
                'is_active': True,
            }
        )
        
        if created:
            system_user.set_unusable_password()
            system_user.save()
            self.stdout.write(self.style.SUCCESS('Created system user for public haunts'))
        
        # Define public haunts
        public_haunts = [
            {
                'name': 'University of Edinburgh - Mastercard Foundation Scholars',
                'url': 'https://global.ed.ac.uk/mastercard-foundation-scholars-program/apply-for-a-scholarship/on-campus-postgraduate-scholarships',
                'description': 'Are they receiving applications for the Mastercard Foundation Scholars Program?',
                'public_slug': 'uoe-mastercard-scholars',
            },
            {
                'name': 'Miles Morland Foundation',
                'url': 'https://milesmorlandfoundation.com/entry-requirements/',
                'description': 'Check if they are accepting applications',
                'public_slug': 'mmf-applications',
            },
            {
                'name': 'AWS re:Invent Conference',
                'url': 'https://reinvent.awsevents.com/',
                'description': 'Check if it is currently happening',
                'public_slug': 'aws-reinvent',
            },
            {
                'name': 'ICANN Fellowship Program',
                'url': 'https://www.icann.org/fellowshipprogram',
                'description': 'Is open for applications',
                'public_slug': 'icann-fellowship',
            },
            {
                'name': 'PyCon US 2026',
                'url': 'https://us.pycon.org/2026/',
                'description': 'Is it accepting proposals currently',
                'public_slug': 'pycon-us-2026',
            },
            {
                'name': 'Devcon Mauritius',
                'url': 'https://conference.mscc.mu/',
                'description': 'Is it happening right now?',
                'public_slug': 'devcon-mauritius',
            },
        ]
        
        if recreate:
            deleted_count = Haunt.objects.filter(owner=system_user, is_public=True).delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing public haunts'))
        
        ai_service = AIConfigService()
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for haunt_data in public_haunts:
                public_slug = haunt_data.pop('public_slug')
                
                # Check if haunt already exists
                existing_haunt = Haunt.objects.filter(
                    public_slug=public_slug,
                    owner=system_user
                ).first()
                
                if existing_haunt and not recreate:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping existing haunt: {haunt_data["name"]}')
                    )
                    continue
                
                self.stdout.write(f'Processing: {haunt_data["name"]}...')
                
                # Generate AI configuration
                try:
                    config = ai_service.generate_config(
                        url=haunt_data['url'],
                        description=haunt_data['description']
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Generated AI config'))
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to generate config: {str(e)}')
                    )
                    # Use fallback config
                    config = {
                        'selectors': {
                            'status': 'body',
                        },
                        'normalization': {},
                        'truthy_values': {},
                    }
                    self.stdout.write(self.style.WARNING(f'  ⚠ Using fallback config'))
                
                # Create or update haunt
                haunt, created = Haunt.objects.update_or_create(
                    public_slug=public_slug,
                    owner=system_user,
                    defaults={
                        'name': haunt_data['name'],
                        'url': haunt_data['url'],
                        'description': haunt_data['description'],
                        'config': config,
                        'is_public': True,
                        'scrape_interval': 60,  # 1 hour
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created public haunt: {haunt.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Updated public haunt: {haunt.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created: {created_count}, Updated: {updated_count}'
            )
        )
