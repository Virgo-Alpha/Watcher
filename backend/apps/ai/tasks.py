"""
Celery tasks for AI-related operations.
"""
import logging
from celery import shared_task
from django.db import transaction

from apps.ai.services import AIConfigService
from apps.rss.models import RSSItem
from watcher.celery import BaseTask

logger = logging.getLogger(__name__)


@shared_task(
    base=BaseTask,
    bind=True,
    name='apps.ai.tasks.generate_summary_async',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30},
    retry_backoff=True,
    retry_jitter=True
)
def generate_summary_async(self, rss_item_id, old_state, new_state):
    """
    Generate AI summary for an RSS item asynchronously.
    This task runs in the background to avoid blocking the scraping workflow.

    Args:
        rss_item_id: UUID of the RSS item to update
        old_state: Previous state dictionary
        new_state: Current state dictionary

    Returns:
        dict: Result with status and summary
    """
    logger.info('Generating AI summary for RSS item: %s', rss_item_id)

    try:
        # Get RSS item
        rss_item = RSSItem.objects.get(id=rss_item_id)

        # Generate summary using AI service
        ai_service = AIConfigService()

        if not ai_service.is_available():
            logger.warning('AI service not available for RSS item %s', rss_item_id)
            return {
                'rss_item_id': str(rss_item_id),
                'status': 'skipped',
                'reason': 'AI service not available'
            }

        summary = ai_service.generate_summary(old_state, new_state)

        # Update RSS item with summary
        with transaction.atomic():
            rss_item.ai_summary = summary
            rss_item.save(update_fields=['ai_summary'])

        logger.info('Successfully generated AI summary for RSS item %s', rss_item_id)

        # Invalidate RSS feed cache
        from apps.rss.services import RSSService
        rss_service = RSSService()
        rss_service.invalidate_feed_cache(rss_item.haunt)

        return {
            'rss_item_id': str(rss_item_id),
            'status': 'success',
            'summary': summary
        }

    except RSSItem.DoesNotExist:
        logger.error('RSS item %s not found', rss_item_id)
        return {
            'rss_item_id': str(rss_item_id),
            'status': 'error',
            'error': 'RSS item not found'
        }

    except Exception as e:
        logger.error('Failed to generate AI summary for RSS item %s: %s', rss_item_id, e)
        # Re-raise to trigger retry
        raise
