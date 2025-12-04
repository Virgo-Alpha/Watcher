import os
import logging
from celery import Celery, Task
from celery.signals import task_failure, task_success, task_retry
from django.conf import settings

logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'watcher.settings.development')

app = Celery('watcher')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'scrape-haunts-15min': {
        'task': 'apps.scraping.tasks.scrape_haunts_by_interval',
        'schedule': 15.0 * 60,  # 15 minutes
        'args': (15,)
    },
    'scrape-haunts-30min': {
        'task': 'apps.scraping.tasks.scrape_haunts_by_interval',
        'schedule': 30.0 * 60,  # 30 minutes
        'args': (30,)
    },
    'scrape-haunts-60min': {
        'task': 'apps.scraping.tasks.scrape_haunts_by_interval',
        'schedule': 60.0 * 60,  # 60 minutes
        'args': (60,)
    },
    'scrape-haunts-daily': {
        'task': 'apps.scraping.tasks.scrape_haunts_by_interval',
        'schedule': 24.0 * 60 * 60,  # 24 hours
        'args': (1440,)  # 1440 minutes = 24 hours
    },
}

app.conf.timezone = 'UTC'

# Task execution settings
app.conf.task_acks_late = True  # Acknowledge tasks after completion
app.conf.task_reject_on_worker_lost = True  # Reject tasks if worker dies
app.conf.worker_prefetch_multiplier = 1  # Fetch one task at a time for long-running tasks
app.conf.task_time_limit = 300  # 5 minutes hard time limit
app.conf.task_soft_time_limit = 240  # 4 minutes soft time limit


class BaseTask(Task):
    """
    Base task class with error handling and logging.
    All Celery tasks should inherit from this class.
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True  # Exponential backoff
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True  # Add randomness to backoff

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Called when task fails after all retries.
        
        Args:
            exc: Exception that caused failure
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info object
        """
        logger.error(
            'Task %s failed after retries: %s',
            self.name,
            exc,
            extra={
                'task_id': task_id,
                'args': args,
                'kwargs': kwargs,
                'exception': str(exc),
            }
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Called when task is retried.
        
        Args:
            exc: Exception that caused retry
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info object
        """
        logger.warning(
            'Task %s retry attempt: %s',
            self.name,
            exc,
            extra={
                'task_id': task_id,
                'args': args,
                'kwargs': kwargs,
                'exception': str(exc),
            }
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """
        Called when task succeeds.
        
        Args:
            retval: Return value of task
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
        """
        logger.info(
            'Task %s completed successfully',
            self.name,
            extra={
                'task_id': task_id,
                'args': args,
                'kwargs': kwargs,
            }
        )
        super().on_success(retval, task_id, args, kwargs)


# Signal handlers for global task monitoring
@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Global handler for task failures"""
    logger.error(
        'Global task failure handler: Task %s failed with exception: %s',
        task_id,
        exception
    )


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Global handler for task success"""
    logger.debug('Global task success handler: Task completed')


@task_retry.connect
def handle_task_retry(sender=None, reason=None, **kwargs):
    """Global handler for task retries"""
    logger.info('Global task retry handler: Task retrying due to: %s', reason)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration"""
    logger.info('Debug task executed: %r', self.request)
    return f'Request: {self.request!r}'