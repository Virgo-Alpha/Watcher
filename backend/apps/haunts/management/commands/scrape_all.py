"""
Management command to manually scrape all haunts in the database.
This is useful for testing and debugging the scraping mechanism.

Usage:
    docker-compose exec web python manage.py scrape_all
    docker-compose exec web python manage.py scrape_all --active-only
    docker-compose exec web python manage.py scrape_all --haunt-id <uuid>
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.haunts.models import Haunt
from apps.scraping.services import ScrapingService, ChangeDetectionService, ScrapingError
from apps.rss.services import RSSService
from apps.ai.services import AIConfigService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually scrape all haunts or a specific haunt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only scrape active haunts',
        )
        parser.add_argument(
            '--haunt-id',
            type=str,
            help='Scrape a specific haunt by ID',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Starting manual scrape of haunts")
        self.stdout.write("=" * 80)
        
        # Get haunts to scrape
        if options['haunt_id']:
            try:
                haunts = Haunt.objects.filter(id=options['haunt_id']).select_related('owner', 'folder')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Invalid haunt ID: {e}"))
                return
        elif options['active_only']:
            haunts = Haunt.objects.filter(is_active=True).select_related('owner', 'folder')
        else:
            haunts = Haunt.objects.all().select_related('owner', 'folder')
        
        total_haunts = haunts.count()
        self.stdout.write(f"\nFound {total_haunts} haunts to scrape\n")
        
        if total_haunts == 0:
            self.stdout.write(self.style.WARNING("No haunts found. Create some haunts first!"))
            return
        
        # Initialize services
        scraping_service = ScrapingService(timeout=30000, use_pool=False)
        change_detection_service = ChangeDetectionService()
        rss_service = RSSService()
        ai_service = AIConfigService()
        
        self.stdout.write(f"AI Service available: {ai_service.is_available()}\n")
        
        # Track results
        results = {
            'total': total_haunts,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        # Scrape each haunt
        for i, haunt in enumerate(haunts, 1):
            self.stdout.write(f"\n[{i}/{total_haunts}] " + "=" * 70)
            
            result = self.scrape_haunt(
                haunt,
                scraping_service,
                change_detection_service,
                rss_service,
                ai_service
            )
            
            results['details'].append(result)
            
            if result['status'] == 'success':
                results['success'] += 1
            elif result['status'] == 'error':
                results['failed'] += 1
            elif result['status'] == 'skipped':
                results['skipped'] += 1
        
        # Print summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SCRAPING SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Total haunts: {results['total']}")
        self.stdout.write(self.style.SUCCESS(f"Successful: {results['success']}"))
        self.stdout.write(self.style.ERROR(f"Failed: {results['failed']}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {results['skipped']}"))
        
        # Print details for failed haunts
        if results['failed'] > 0:
            self.stdout.write("\nFailed haunts:")
            for result in results['details']:
                if result['status'] == 'error':
                    self.stdout.write(self.style.ERROR(
                        f"  - {result['name']} ({result['haunt_id']}): {result.get('error', 'Unknown error')}"
                    ))
        
        # Print details for successful haunts with changes
        changes_detected = [r for r in results['details'] if r.get('has_changes')]
        if changes_detected:
            self.stdout.write(f"\nHaunts with changes detected: {len(changes_detected)}")
            for result in changes_detected:
                self.stdout.write(self.style.SUCCESS(
                    f"  - {result['name']}: {result['changes_count']} changes"
                ))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("Scraping complete!"))
        self.stdout.write("=" * 80)

    def scrape_haunt(self, haunt, scraping_service, change_detection_service, rss_service, ai_service):
        """
        Scrape a single haunt and process changes
        
        Args:
            haunt: Haunt instance to scrape
            scraping_service: ScrapingService instance
            change_detection_service: ChangeDetectionService instance
            rss_service: RSSService instance
            ai_service: AIConfigService instance
        
        Returns:
            dict: Result of scraping operation
        """
        self.stdout.write(f"Scraping haunt: {haunt.name} ({haunt.id})")
        self.stdout.write(f"  URL: {haunt.url}")
        self.stdout.write(f"  Active: {haunt.is_active}")
        
        if not haunt.is_active:
            self.stdout.write(self.style.WARNING("  Skipping inactive haunt"))
            return {
                'haunt_id': str(haunt.id),
                'name': haunt.name,
                'status': 'skipped',
                'reason': 'inactive'
            }
        
        if not haunt.config or 'selectors' not in haunt.config:
            self.stdout.write(self.style.WARNING("  Skipping haunt without configuration"))
            return {
                'haunt_id': str(haunt.id),
                'name': haunt.name,
                'status': 'skipped',
                'reason': 'no_config'
            }
        
        try:
            # Scrape the URL
            self.stdout.write("  Scraping URL...")
            new_state = scraping_service.scrape_url(haunt.url, haunt.config)
            self.stdout.write(f"  Extracted {len(new_state)} fields: {list(new_state.keys())}")
            
            # Display extracted data
            for key, value in new_state.items():
                self.stdout.write(f"    {key}: {value}")
            
            # Detect changes
            old_state = haunt.current_state or {}
            has_changes, changes = change_detection_service.detect_changes(old_state, new_state)
            
            self.stdout.write(f"  Changes detected: {has_changes}")
            if has_changes:
                self.stdout.write(f"  Number of changes: {len(changes)}")
                for key, change in changes.items():
                    self.stdout.write(f"    {key}: {change['old']} → {change['new']}")
            
            # Use AI to determine if alert should be sent
            should_alert = False
            ai_summary = None
            alert_reason = "No changes detected"
            
            if has_changes:
                # AI evaluates if changes match user's intent
                evaluation = ai_service.evaluate_alert_decision(
                    user_description=haunt.description,
                    old_state=old_state,
                    new_state=new_state,
                    changes=changes
                )
                
                should_alert = evaluation['should_alert']
                alert_reason = evaluation['reason']
                ai_summary = evaluation['summary']
                
                self.stdout.write(f"  AI Decision: {'ALERT' if should_alert else 'NO ALERT'}")
                self.stdout.write(f"  Confidence: {evaluation['confidence']}")
                self.stdout.write(f"  Reason: {alert_reason}")
                self.stdout.write(f"  Summary: {ai_summary}")
            
            # Create RSS item if alert should be sent
            rss_item_created = False
            if should_alert:
                self.stdout.write("  Creating RSS item...")
                
                # Create RSS item with AI summary
                rss_item = rss_service.create_rss_item(
                    haunt=haunt,
                    changes=changes,
                    ai_summary=ai_summary if haunt.enable_ai_summary else None
                )
                rss_item_created = True
                self.stdout.write(f"  Created RSS item: {rss_item.id}")
            
            # Update haunt state
            self.stdout.write("  Updating haunt state...")
            haunt.current_state = new_state
            haunt.last_scraped_at = timezone.now()
            haunt.reset_error_count()
            
            # Update alert state when alert is sent
            if should_alert:
                haunt.last_alert_state = new_state
                self.stdout.write("  Updated alert state")
            
            haunt.save(update_fields=[
                'current_state',
                'last_scraped_at',
                'error_count',
                'last_error',
                'last_alert_state'
            ])
            
            self.stdout.write(self.style.SUCCESS("  ✓ Successfully scraped haunt"))
            
            return {
                'haunt_id': str(haunt.id),
                'name': haunt.name,
                'status': 'success',
                'fields_extracted': len(new_state),
                'has_changes': has_changes,
                'changes_count': len(changes),
                'should_alert': should_alert,
                'rss_item_created': rss_item_created,
                'ai_summary': ai_summary
            }
            
        except ScrapingError as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Scraping failed: {e}"))
            haunt.increment_error_count(str(e))
            haunt.last_scraped_at = timezone.now()
            haunt.save(update_fields=['error_count', 'last_error', 'last_scraped_at'])
            
            return {
                'haunt_id': str(haunt.id),
                'name': haunt.name,
                'status': 'error',
                'error': str(e)
            }
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Unexpected error: {e}"))
            haunt.increment_error_count(f'Unexpected error: {str(e)}')
            haunt.last_scraped_at = timezone.now()
            haunt.save(update_fields=['error_count', 'last_error', 'last_scraped_at'])
            
            return {
                'haunt_id': str(haunt.id),
                'name': haunt.name,
                'status': 'error',
                'error': str(e)
            }
