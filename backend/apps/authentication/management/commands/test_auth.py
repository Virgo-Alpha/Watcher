"""
Django management command to run authentication app tests.
"""
from django.core.management.base import BaseCommand
from django.test.utils import get_runner
from django.conf import settings
import sys


class Command(BaseCommand):
    """Management command to run authentication app tests."""
    
    help = 'Run tests for the authentication app'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--verbosity',
            type=int,
            default=2,
            help='Verbosity level for test output'
        )
        parser.add_argument(
            '--failfast',
            action='store_true',
            help='Stop on first test failure'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            default='test_*.py',
            help='Test file pattern to match'
        )
        parser.add_argument(
            '--module',
            type=str,
            help='Specific test module to run'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        verbosity = options['verbosity']
        failfast = options['failfast']
        pattern = options['pattern']
        module = options['module']
        
        self.stdout.write(
            self.style.SUCCESS('Running authentication app tests...')
        )
        
        # Get the test runner
        TestRunner = get_runner(settings)
        test_runner = TestRunner(
            verbosity=verbosity,
            interactive=False,
            failfast=failfast
        )
        
        # Determine test labels
        if module:
            test_labels = [f'apps.authentication.tests.{module}']
        else:
            test_labels = ['apps.authentication.tests']
        
        # Run tests
        failures = test_runner.run_tests(test_labels)
        
        if failures:
            self.stdout.write(
                self.style.ERROR(f'Tests failed with {failures} failures')
            )
            sys.exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS('All tests passed!')
            )
            sys.exit(0)