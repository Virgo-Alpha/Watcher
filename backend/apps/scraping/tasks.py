"""
Celery tasks for scheduled scraping operations.
"""
import logging
import time
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from apps.haunts.models import Haunt
from apps.scraping.services import ScrapingService, ChangeDetectionService, ScrapingError
from apps.common.metrics import MetricsCollector
from watcher.celery import BaseTask

logger = logging.getLogger(__name__)


@shared_task(base=BaseTask, bind=True, name='apps.scraping.tasks.scrape_haunts_by_interval')
def scrape_haunts_by_interval(self, interval_minutes):
    """
    Scrape haunts based on their configured interval.
    This task is called periodically by Celery Beat for each interval.
    
    Args:
        interval_minutes: Scrape interval in minutes (15, 30, 60, or 1440)
    
    Returns:
        dict: Summary of scraping results
    """
    logger.info('Starting scrape for interval: %s minutes', interval_minutes)
    
    # Query haunts that match this interval and are active
    haunts = Haunt.objects.filter(
        scrape_interval=interval_minutes,
        is_active=True
    ).select_related('owner', 'folder')
    
    total_haunts = haunts.count()
    logger.info('Found %s haunts to scrape for interval %s', total_haunts, interval_minutes)
    
    if total_haunts == 0:
        return {
            'interval': interval_minutes,
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    # Track results
    results = {
        'interval': interval_minutes,
        'total': total_haunts,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # Process each haunt
    for haunt in haunts:
        try:
            # Check if haunt should be scraped (avoid too frequent scraping)
            if should_skip_scrape(haunt, interval_minutes):
                logger.debug('Skipping haunt %s - scraped too recently', haunt.id)
                results['skipped'] += 1
                continue
            
            # Trigger individual haunt scrape
            scrape_haunt.delay(str(haunt.id))
            results['success'] += 1
            
        except Exception as e:
            logger.error('Error queuing scrape for haunt %s: %s', haunt.id, e)
            results['failed'] += 1
            results['errors'].append({
                'haunt_id': str(haunt.id),
                'error': str(e)
            })
    
    logger.info(
        'Completed scrape scheduling for interval %s: %s success, %s failed, %s skipped',
        interval_minutes,
        results['success'],
        results['failed'],
        results['skipped']
    )
    
    return results


def should_skip_scrape(haunt, interval_minutes):
    """
    Determine if a haunt should be skipped based on last scrape time.
    
    Args:
        haunt: Haunt instance
        interval_minutes: Configured scrape interval
    
    Returns:
        bool: True if scrape should be skipped
    """
    if not haunt.last_scraped_at:
        return False
    
    # Calculate minimum time between scrapes (90% of interval to allow some flexibility)
    min_interval = timedelta(minutes=interval_minutes * 0.9)
    time_since_last_scrape = timezone.now() - haunt.last_scraped_at
    
    return time_since_last_scrape < min_interval


@shared_task(
    base=BaseTask,
    bind=True,
    name='apps.scraping.tasks.scrape_haunt',
    autoretry_for=(ScrapingError,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def scrape_haunt(self, haunt_id):
    """
    Scrape a single haunt, detect changes, and create RSS items.
    This task handles the complete scraping workflow with change detection.
    
    Args:
        haunt_id: UUID of the haunt to scrape
    
    Returns:
        dict: Scraping result with status and data
    
    Raises:
        ScrapingError: If scraping fails after retries
    """
    logger.info('Starting scrape for haunt: %s', haunt_id)
    
    # Track scrape duration
    start_time = time.time()
    
    try:
        # Get haunt from database
        haunt = Haunt.objects.select_for_update().get(id=haunt_id)
        
        if not haunt.is_active:
            logger.info('Haunt %s is not active, skipping', haunt_id)
            return {
                'haunt_id': haunt_id,
                'status': 'skipped',
                'reason': 'inactive'
            }
        
        # Initialize services
        scraping_service = ScrapingService(timeout=30000, use_pool=True)
        change_detection_service = ChangeDetectionService()
        
        # Scrape the URL
        try:
            new_state = scraping_service.scrape_url(haunt.url, haunt.config)
            logger.info('Successfully scraped haunt %s: %s fields extracted', haunt_id, len(new_state))
            
        except ScrapingError as e:
            logger.error('Scraping failed for haunt %s: %s', haunt_id, e)
            
            # Record failure metric
            duration_ms = (time.time() - start_time) * 1000
            MetricsCollector.record_scrape_failure(haunt_id, e.__class__.__name__)
            
            # Update error tracking
            with transaction.atomic():
                haunt.increment_error_count(str(e))
                haunt.last_scraped_at = timezone.now()
                haunt.save(update_fields=['error_count', 'last_error', 'last_scraped_at'])
            
            # Re-raise to trigger retry
            raise
        
        # Detect changes
        old_state = haunt.current_state or {}
        has_changes, changes = change_detection_service.detect_changes(old_state, new_state)
        
        logger.info('Change detection for haunt %s: has_changes=%s, changes=%s', 
                   haunt_id, has_changes, len(changes))
        
        # Use AI to determine if alert should be sent
        should_alert = False
        ai_summary = None
        alert_reason = "No changes detected"
        
        if has_changes:
            from apps.ai.services import AIConfigService
            ai_service = AIConfigService()
            
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
            
            logger.info(
                'AI alert decision for haunt %s: should_alert=%s, confidence=%s, reason=%s',
                haunt_id, should_alert, evaluation['confidence'], alert_reason
            )
        
        # Create RSS item if alert should be sent
        rss_item_created = False
        email_sent = False
        if should_alert:
            from apps.rss.services import RSSService, EmailNotificationService
            
            rss_service = RSSService()
            email_service = EmailNotificationService()

            try:
                # Create RSS item with AI summary already generated
                rss_item = rss_service.create_rss_item(
                    haunt=haunt,
                    changes=changes,
                    ai_summary=ai_summary if haunt.enable_ai_summary else None
                )
                rss_item_created = True
                logger.info('Created RSS item %s for haunt %s with AI summary', rss_item.id, haunt_id)
                
                # Send email notifications
                try:
                    email_result = email_service.send_change_notification(rss_item)
                    email_sent = email_result['sent'] > 0
                    logger.info(
                        'Email notifications for haunt %s: %s sent, %s failed',
                        haunt_id, email_result['sent'], email_result['failed']
                    )
                except Exception as email_error:
                    logger.error('Failed to send email notifications for haunt %s: %s', haunt_id, email_error)

            except Exception as e:
                logger.error('Failed to create RSS item for haunt %s: %s', haunt_id, e)
        
        # Update haunt state
        with transaction.atomic():
            haunt.current_state = new_state
            haunt.last_scraped_at = timezone.now()
            haunt.reset_error_count()
            
            # Update alert state when alert is sent (for tracking purposes)
            if should_alert:
                haunt.last_alert_state = new_state
                logger.info('Updated alert state for haunt %s', haunt_id)
            
            haunt.save(update_fields=[
                'current_state', 
                'last_scraped_at', 
                'error_count', 
                'last_error',
                'last_alert_state'
            ])
        
        logger.info('Successfully updated state for haunt %s', haunt_id)
        
        # Record success metric
        duration_ms = (time.time() - start_time) * 1000
        MetricsCollector.record_scrape_success(haunt_id, duration_ms)
        
        return {
            'haunt_id': haunt_id,
            'status': 'success',
            'fields_extracted': len(new_state),
            'has_changes': has_changes,
            'changes_count': len(changes),
            'should_alert': should_alert,
            'rss_item_created': rss_item_created,
            'email_sent': email_sent,
            'scraped_at': timezone.now().isoformat(),
            'duration_ms': round(duration_ms, 2)
        }
        
    except Haunt.DoesNotExist:
        logger.error('Haunt %s not found', haunt_id)
        return {
            'haunt_id': haunt_id,
            'status': 'error',
            'error': 'Haunt not found'
        }
    
    except ScrapingError:
        # Re-raise scraping errors to trigger retry
        raise
    
    except Exception as e:
        logger.error('Unexpected error scraping haunt %s: %s', haunt_id, e, exc_info=True)
        
        # Update error tracking
        try:
            with transaction.atomic():
                haunt = Haunt.objects.select_for_update().get(id=haunt_id)
                haunt.increment_error_count(f'Unexpected error: {str(e)}')
                haunt.last_scraped_at = timezone.now()
                haunt.save(update_fields=['error_count', 'last_error', 'last_scraped_at'])
        except Exception as update_error:
            logger.error('Failed to update error count: %s', update_error)
        
        return {
            'haunt_id': haunt_id,
            'status': 'error',
            'error': str(e)
        }


@shared_task(base=BaseTask, bind=True, name='apps.scraping.tasks.scrape_haunt_manual')
def scrape_haunt_manual(self, haunt_id):
    """
    Manually trigger a scrape for a specific haunt.
    This is called when a user manually refreshes a haunt.
    
    Args:
        haunt_id: UUID of the haunt to scrape
    
    Returns:
        dict: Scraping result
    """
    logger.info('Manual scrape triggered for haunt: %s', haunt_id)
    
    # Delegate to main scrape task
    return scrape_haunt(haunt_id)