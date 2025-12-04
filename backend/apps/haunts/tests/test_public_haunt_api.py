"""
Tests for public haunt management API endpoints.
Tests Requirements 8.2, 8.3, 8.4
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Folder, Haunt

User = get_user_model()


class PublicHauntAPITestCase(TestCase):
    """Test case for public haunt management API"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        # Create test haunts for user1
        self.private_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Private Haunt',
            url='https://example.com/private',
            description='Private haunt description',
            is_public=False,
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {'status': {'type': 'text'}},
                'truthy_values': {'status': ['open']}
            }
        )

        self.public_haunt1 = Haunt.objects.create(
            owner=self.user1,
            name='Public Haunt 1',
            url='https://example.com/public1',
            description='First public haunt',
            is_public=True,
            config={
                'selectors': {'price': 'css:.price'},
                'normalization': {'price': {'type': 'number'}},
                'truthy_values': {'price': []}
            }
        )

        self.public_haunt2 = Haunt.objects.create(
            owner=self.user2,
            name='Public Haunt 2',
            url='https://example.com/public2',
            description='Second public haunt',
            is_public=True,
            is_active=True
        )

        # Create inactive public haunt (should not appear in directory)
        self.inactive_public_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Inactive Public Haunt',
            url='https://example.com/inactive',
            is_public=True,
            is_active=False
        )

    def authenticate_user1(self):
        """Authenticate as user1"""
        self.client.force_authenticate(user=self.user1)

    def authenticate_user2(self):
        """Authenticate as user2"""
        self.client.force_authenticate(user=self.user2)

    # Tests for make_public endpoint (Requirement 8.2)

    def test_make_haunt_public(self):
        """Test making a private haunt public generates public_slug"""
        self.authenticate_user1()

        # Verify haunt is private initially
        self.assertFalse(self.private_haunt.is_public)
        self.assertIsNone(self.private_haunt.public_slug)

        url = reverse('haunt-make-public', kwargs={'pk': self.private_haunt.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('public_slug', response.data)
        self.assertIn('public_url', response.data)
        self.assertIsNotNone(response.data['public_slug'])

        # Verify in database
        self.private_haunt.refresh_from_db()
        self.assertTrue(self.private_haunt.is_public)
        self.assertIsNotNone(self.private_haunt.public_slug)
        self.assertEqual(self.private_haunt.public_slug, response.data['public_slug'])

    def test_make_haunt_public_generates_unique_slug(self):
        """Test that public_slug is unique and based on haunt name"""
        self.authenticate_user1()

        url = reverse('haunt-make-public', kwargs={'pk': self.private_haunt.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        public_slug = response.data['public_slug']

        # Slug should be based on haunt name
        self.assertIn('private-haunt', public_slug.lower())

    def test_make_already_public_haunt_public(self):
        """Test making an already public haunt public returns existing slug"""
        self.authenticate_user1()

        original_slug = self.public_haunt1.public_slug

        url = reverse('haunt-make-public', kwargs={'pk': self.public_haunt1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['public_slug'], original_slug)
        self.assertIn('already public', response.data['message'].lower())

    def test_make_public_requires_authentication(self):
        """Test that making haunt public requires authentication"""
        url = reverse('haunt-make-public', kwargs={'pk': self.private_haunt.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_make_public_requires_ownership(self):
        """Test that only owner can make haunt public"""
        self.authenticate_user2()

        url = reverse('haunt-make-public', kwargs={'pk': self.private_haunt.id})
        response = self.client.post(url)

        # Should return 404 since user2 doesn't own this haunt
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify haunt is still private
        self.private_haunt.refresh_from_db()
        self.assertFalse(self.private_haunt.is_public)

    def test_make_private(self):
        """Test making a public haunt private removes public_slug"""
        self.authenticate_user1()

        # Verify haunt is public initially
        self.assertTrue(self.public_haunt1.is_public)
        self.assertIsNotNone(self.public_haunt1.public_slug)

        url = reverse('haunt-make-private', kwargs={'pk': self.public_haunt1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('successfully made private', response.data['message'].lower())

        # Verify in database
        self.public_haunt1.refresh_from_db()
        self.assertFalse(self.public_haunt1.is_public)
        self.assertIsNone(self.public_haunt1.public_slug)

    def test_make_already_private_haunt_private(self):
        """Test making an already private haunt private"""
        self.authenticate_user1()

        url = reverse('haunt-make-private', kwargs={'pk': self.private_haunt.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('already private', response.data['message'].lower())

    # Tests for public haunt directory (Requirement 8.3)

    def test_list_public_haunts_unauthenticated(self):
        """Test listing public haunts without authentication"""
        url = reverse('public-haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only active public haunts
        self.assertEqual(response.data['count'], 2)  # public_haunt1 and public_haunt2

        haunt_names = [haunt['name'] for haunt in response.data['results']]
        self.assertIn('Public Haunt 1', haunt_names)
        self.assertIn('Public Haunt 2', haunt_names)
        self.assertNotIn('Private Haunt', haunt_names)
        self.assertNotIn('Inactive Public Haunt', haunt_names)

    def test_list_public_haunts_authenticated(self):
        """Test listing public haunts with authentication"""
        self.authenticate_user1()

        url = reverse('public-haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_list_public_haunts_excludes_inactive(self):
        """Test that inactive public haunts are excluded from directory"""
        url = reverse('public-haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        haunt_names = [haunt['name'] for haunt in response.data['results']]
        self.assertNotIn('Inactive Public Haunt', haunt_names)

    def test_list_public_haunts_search(self):
        """Test searching public haunts by name, description, or URL"""
        url = reverse('public-haunt-list')

        # Search by name
        response = self.client.get(url, {'search': 'Public Haunt 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Public Haunt 1')

        # Search by description
        response = self.client.get(url, {'search': 'First public'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Public Haunt 1')

        # Search by URL
        response = self.client.get(url, {'search': 'public2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Public Haunt 2')

    def test_list_public_haunts_filter_by_owner(self):
        """Test filtering public haunts by owner username"""
        url = reverse('public-haunt-list')

        # Filter by user1
        response = self.client.get(url, {'owner': 'user1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Public Haunt 1')

        # Filter by user2
        response = self.client.get(url, {'owner': 'user2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Public Haunt 2')

    # Tests for public haunt detail (Requirement 8.4)

    def test_retrieve_public_haunt_by_slug_unauthenticated(self):
        """Test retrieving public haunt by slug without authentication"""
        url = reverse('public-haunt-detail', kwargs={'public_slug': self.public_haunt1.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Public Haunt 1')
        self.assertEqual(response.data['url'], 'https://example.com/public1')
        self.assertEqual(response.data['public_slug'], self.public_haunt1.public_slug)
        self.assertTrue(response.data['is_public'])

    def test_retrieve_public_haunt_by_slug_authenticated(self):
        """Test retrieving public haunt by slug with authentication"""
        self.authenticate_user2()

        url = reverse('public-haunt-detail', kwargs={'public_slug': self.public_haunt1.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Public Haunt 1')

    def test_retrieve_nonexistent_public_haunt(self):
        """Test retrieving non-existent public haunt returns 404"""
        url = reverse('public-haunt-detail', kwargs={'public_slug': 'nonexistent-slug'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['error'].lower())

    def test_retrieve_private_haunt_by_slug_fails(self):
        """Test that private haunts cannot be accessed via public endpoint"""
        # Make sure private haunt has no public_slug
        self.assertIsNone(self.private_haunt.public_slug)

        # Try to access with a fake slug
        url = reverse('public-haunt-detail', kwargs={'public_slug': 'fake-slug'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_inactive_public_haunt_fails(self):
        """Test that inactive public haunts cannot be accessed"""
        url = reverse('public-haunt-detail', kwargs={'public_slug': self.inactive_public_haunt.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Tests for public haunt visibility and access controls

    def test_public_haunt_includes_rss_url(self):
        """Test that public haunt detail includes RSS URL"""
        url = reverse('public-haunt-detail', kwargs={'public_slug': self.public_haunt1.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rss_url', response.data)
        self.assertIn('public', response.data['rss_url'])
        self.assertIn(self.public_haunt1.public_slug, response.data['rss_url'])

    def test_public_haunt_includes_public_url(self):
        """Test that public haunt detail includes public URL"""
        url = reverse('public-haunt-detail', kwargs={'public_slug': self.public_haunt1.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('public_url', response.data)
        self.assertIsNotNone(response.data['public_url'])

    def test_public_haunt_viewset_is_read_only(self):
        """Test that public haunt viewset only allows read operations"""
        self.authenticate_user1()

        # Try to create via public endpoint
        url = reverse('public-haunt-list')
        data = {
            'name': 'New Public Haunt',
            'url': 'https://example.com/new'
        }
        response = self.client.post(url, data, format='json')

        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try to update via public endpoint
        url = reverse('public-haunt-detail', kwargs={'public_slug': self.public_haunt1.public_slug})
        data = {
            'name': 'Updated Name'
        }
        response = self.client.patch(url, data, format='json')

        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try to delete via public endpoint
        response = self.client.delete(url)

        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_public_slug_uniqueness(self):
        """Test that public slugs are unique across all haunts"""
        self.authenticate_user1()

        # Create two haunts with the same name
        haunt1 = Haunt.objects.create(
            owner=self.user1,
            name='Duplicate Name',
            url='https://example.com/dup1',
            is_public=True
        )

        haunt2 = Haunt.objects.create(
            owner=self.user1,
            name='Duplicate Name',
            url='https://example.com/dup2',
            is_public=True
        )

        # Slugs should be different
        self.assertNotEqual(haunt1.public_slug, haunt2.public_slug)

        # Both should be accessible
        url1 = reverse('public-haunt-detail', kwargs={'public_slug': haunt1.public_slug})
        response1 = self.client.get(url1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        url2 = reverse('public-haunt-detail', kwargs={'public_slug': haunt2.public_slug})
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_public_haunt_directory_pagination(self):
        """Test that public haunt directory supports pagination"""
        # Create many public haunts
        for i in range(60):
            Haunt.objects.create(
                owner=self.user1,
                name=f'Public Haunt {i}',
                url=f'https://example.com/haunt{i}',
                is_public=True
            )

        url = reverse('public-haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

        # Should have pagination
        self.assertGreater(response.data['count'], 50)
        self.assertLessEqual(len(response.data['results']), 50)  # Default page size

    def test_make_public_then_retrieve_via_public_endpoint(self):
        """Test end-to-end flow: make haunt public then retrieve it"""
        self.authenticate_user1()

        # Make haunt public
        make_public_url = reverse('haunt-make-public', kwargs={'pk': self.private_haunt.id})
        make_public_response = self.client.post(make_public_url)

        self.assertEqual(make_public_response.status_code, status.HTTP_200_OK)
        public_slug = make_public_response.data['public_slug']

        # Retrieve via public endpoint (without authentication)
        self.client.force_authenticate(user=None)
        retrieve_url = reverse('public-haunt-detail', kwargs={'public_slug': public_slug})
        retrieve_response = self.client.get(retrieve_url)

        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['name'], 'Private Haunt')
        self.assertTrue(retrieve_response.data['is_public'])
