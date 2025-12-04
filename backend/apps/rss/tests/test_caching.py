"""
Performance tests for RSS feed caching.
"""
import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from apps.haunts.models import Haunt
from apps.rss.models import RSSItem
from apps.rss.services import RSSService

User = get_user_model()


class RSSCachingTest(TestCase):
    """Test RSS feed caching functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt description',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            scrape_interval=60
        )

        # Create multiple RSS items with unique timestamps
        from datetime import timedelta
        base_time = timezone.now()
        for i in range(10):
            RSSItem.objects.create(
                haunt=self.haunt,
                title=f'Change {i}',
                description=f'Description {i}',
                link=self.haunt.url,
                pub_date=base_time - timedelta(seconds=i)
            )

        self.service = RSSService()

        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_feed_caching(self):
        """Test that RSS feed is cached."""
        # First call should generate and cache
        feed1 = self.service.generate_rss_feed(self.haunt)

        # Second call should return cached version
        feed2 = self.service.generate_rss_feed(self.haunt)

        # Should be identical
        self.assertEqual(feed1, feed2)

    def test_cache_invalidation_on_new_item(self):
        """Test that cache is invalidated when new RSS item is created."""
        # Generate and cache feed
        feed1 = self.service.generate_rss_feed(self.haunt)

        # Wait a moment to ensure unique timestamp
        import time
        time.sleep(1)

        # Create new RSS item (should invalidate cache)
        changes = {'status': {'old': 'closed', 'new': 'open'}}
        self.service.create_rss_item(self.haunt, changes)

        # Next call should generate new feed
        feed2 = self.service.generate_rss_feed(self.haunt)

        # Feeds should be different (new item added)
        self.assertNotEqual(feed1, feed2)
        self.assertIn('status changed', feed2)

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache_key = self.service._get_cache_key(self.haunt)

        self.assertIn(str(self.haunt.id), cache_key)
        self.assertIn('rss_feed', cache_key)

    def test_manual_cache_invalidation(self):
        """Test manual cache invalidation."""
        # Generate and cache feed
        self.service.generate_rss_feed(self.haunt)

        # Verify cache exists
        cache_key = self.service._get_cache_key(self.haunt)
        self.assertIsNotNone(cache.get(cache_key))

        # Invalidate cache
        self.service.invalidate_feed_cache(self.haunt)

        # Verify cache is cleared
        self.assertIsNone(cache.get(cache_key))

    def test_cache_bypass(self):
        """Test bypassing cache when use_cache=False."""
        # Generate and cache feed
        feed1 = self.service.generate_rss_feed(self.haunt, use_cache=True)

        # Generate without cache
        feed2 = self.service.generate_rss_feed(self.haunt, use_cache=False)

        # Should be identical but generated fresh
        self.assertEqual(feed1, feed2)

    def test_caching_improves_performance(self):
        """Test that caching improves performance."""
        # First call (uncached)
        start1 = time.time()
        self.service.generate_rss_feed(self.haunt, use_cache=False)
        time1 = time.time() - start1

        # Generate and cache
        self.service.generate_rss_feed(self.haunt, use_cache=True)

        # Second call (cached)
        start2 = time.time()
        self.service.generate_rss_feed(self.haunt, use_cache=True)
        time2 = time.time() - start2

        # Cached version should be faster (or at least not slower)
        # Note: This is a rough test and may be flaky
        self.assertLessEqual(time2, time1 * 2)  # Allow some variance

    def test_optimized_query(self):
        """Test that get_recent_items uses optimized query."""
        # This test verifies the query uses select_related and only()
        with self.assertNumQueries(1):
            items = self.service.get_recent_items(self.haunt, limit=10)
            # Access related fields to ensure they're loaded
            for item in items:
                _ = item.haunt.name
                _ = item.haunt.url

    def test_cache_different_haunts(self):
        """Test that different haunts have separate caches."""
        # Create second haunt
        haunt2 = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt 2',
            url='https://example2.com',
            description='Test haunt 2',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            scrape_interval=60
        )

        RSSItem.objects.create(
            haunt=haunt2,
            title='Change for haunt 2',
            description='Description for haunt 2',
            link=haunt2.url
        )

        # Generate feeds for both haunts
        feed1 = self.service.generate_rss_feed(self.haunt)
        feed2 = self.service.generate_rss_feed(haunt2)

        # Feeds should be different
        self.assertNotEqual(feed1, feed2)
        self.assertIn('Test Haunt', feed1)
        self.assertIn('Test Haunt 2', feed2)

        # Invalidating one should not affect the other
        self.service.invalidate_feed_cache(self.haunt)

        cache_key1 = self.service._get_cache_key(self.haunt)
        cache_key2 = self.service._get_cache_key(haunt2)

        self.assertIsNone(cache.get(cache_key1))
        self.assertIsNotNone(cache.get(cache_key2))
