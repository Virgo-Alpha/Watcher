"""
Tests for haunt management API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Folder, Haunt

User = get_user_model()


class HauntAPITestCase(TestCase):
    """Test case for haunt management API"""

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

        # Create test folders
        self.folder1 = Folder.objects.create(
            user=self.user1,
            name='Work'
        )
        self.folder2 = Folder.objects.create(
            user=self.user1,
            name='Personal'
        )

        # Create test haunts for user1
        self.haunt1 = Haunt.objects.create(
            owner=self.user1,
            name='Test Haunt 1',
            url='https://example.com/1',
            description='Test description 1',
            folder=self.folder1,
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {'status': {'type': 'text'}},
                'truthy_values': {'status': ['open']}
            }
        )
        self.haunt2 = Haunt.objects.create(
            owner=self.user1,
            name='Test Haunt 2',
            url='https://example.com/2',
            description='Test description 2',
            is_active=False
        )
        self.public_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Public Haunt',
            url='https://example.com/public',
            is_public=True
        )

        # Create haunt for user2
        self.user2_haunt = Haunt.objects.create(
            owner=self.user2,
            name='User2 Haunt',
            url='https://example.com/user2'
        )

    def authenticate_user1(self):
        """Authenticate as user1"""
        self.client.force_authenticate(user=self.user1)

    def authenticate_user2(self):
        """Authenticate as user2"""
        self.client.force_authenticate(user=self.user2)

    def test_list_haunts_authenticated(self):
        """Test listing haunts for authenticated user"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With pagination, response.data is a dict with 'results' key
        self.assertEqual(response.data['count'], 3)  # 3 haunts for user1
        self.assertEqual(len(response.data['results']), 3)

        # Check haunt names
        haunt_names = [haunt['name'] for haunt in response.data['results']]
        self.assertIn('Test Haunt 1', haunt_names)
        self.assertIn('Test Haunt 2', haunt_names)
        self.assertIn('Public Haunt', haunt_names)

    def test_list_haunts_unauthenticated(self):
        """Test listing haunts without authentication"""
        url = reverse('haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_haunts_user_isolation(self):
        """Test that users only see their own haunts"""
        self.authenticate_user2()
        url = reverse('haunt-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only 1 haunt for user2
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'User2 Haunt')

    def test_list_haunts_filter_by_folder(self):
        """Test filtering haunts by folder"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        response = self.client.get(url, {'folder': self.folder1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Haunt 1')

    def test_list_haunts_filter_by_no_folder(self):
        """Test filtering haunts without folder"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        response = self.client.get(url, {'folder': 'none'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return haunts without folder
        haunt_names = [haunt['name'] for haunt in response.data['results']]
        self.assertIn('Test Haunt 2', haunt_names)
        self.assertIn('Public Haunt', haunt_names)
        self.assertNotIn('Test Haunt 1', haunt_names)

    def test_list_haunts_filter_by_active_status(self):
        """Test filtering haunts by active status"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        response = self.client.get(url, {'is_active': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return active haunts
        for haunt in response.data['results']:
            self.assertTrue(haunt['is_active'])

    def test_create_haunt(self):
        """Test creating a new haunt"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        data = {
            'name': 'New Haunt',
            'url': 'https://example.com/new',
            'description': 'New haunt description',
            'config': {
                'selectors': {'price': 'css:.price'},
                'normalization': {'price': {'type': 'number'}},
                'truthy_values': {'price': []}
            },
            'scrape_interval': 30,
            'alert_mode': 'on_change'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Haunt')
        self.assertEqual(response.data['url'], 'https://example.com/new')
        self.assertEqual(response.data['scrape_interval'], 30)

        # Verify haunt was created in database
        haunt = Haunt.objects.get(id=response.data['id'])
        self.assertEqual(haunt.owner, self.user1)
        self.assertEqual(haunt.name, 'New Haunt')

    def test_create_haunt_with_folder(self):
        """Test creating a haunt with folder assignment"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        data = {
            'name': 'Haunt with Folder',
            'url': 'https://example.com/folder',
            'folder': self.folder1.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['folder'], self.folder1.id)

        # Verify in database
        haunt = Haunt.objects.get(id=response.data['id'])
        self.assertEqual(haunt.folder, self.folder1)

    def test_create_haunt_invalid_folder(self):
        """Test creating haunt with folder from different user"""
        self.authenticate_user1()

        # Create folder for user2
        user2_folder = Folder.objects.create(
            user=self.user2,
            name='User2 Folder'
        )

        url = reverse('haunt-list')
        data = {
            'name': 'Invalid Haunt',
            'url': 'https://example.com/invalid',
            'folder': user2_folder.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('folder', response.data)

    def test_create_haunt_invalid_config(self):
        """Test creating haunt with invalid configuration"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        data = {
            'name': 'Invalid Config Haunt',
            'url': 'https://example.com/invalid',
            'config': {
                'selectors': {}  # Missing required keys
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('config', response.data)

    def test_retrieve_haunt(self):
        """Test retrieving a single haunt"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.haunt1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Haunt 1')
        self.assertEqual(response.data['url'], 'https://example.com/1')
        self.assertIn('config', response.data)
        self.assertIn('folder_name', response.data)

    def test_retrieve_other_user_haunt(self):
        """Test retrieving another user's private haunt"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.user2_haunt.id})
        response = self.client.get(url)

        # Should return 404 since user1 doesn't own this haunt
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_haunt(self):
        """Test updating a haunt"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.haunt1.id})
        data = {
            'name': 'Updated Haunt Name',
            'scrape_interval': 60
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Haunt Name')
        self.assertEqual(response.data['scrape_interval'], 60)

        # Verify in database
        self.haunt1.refresh_from_db()
        self.assertEqual(self.haunt1.name, 'Updated Haunt Name')
        self.assertEqual(self.haunt1.scrape_interval, 60)

    def test_update_other_user_haunt(self):
        """Test updating another user's haunt"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.user2_haunt.id})
        data = {
            'name': 'Hacked Name'
        }
        response = self.client.patch(url, data, format='json')

        # Should return 404 since user1 doesn't own this haunt
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_haunt(self):
        """Test deleting a haunt"""
        self.authenticate_user1()

        # Create a haunt to delete
        haunt_to_delete = Haunt.objects.create(
            owner=self.user1,
            name='To Delete',
            url='https://example.com/delete'
        )

        url = reverse('haunt-detail', kwargs={'pk': haunt_to_delete.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify haunt was deleted
        self.assertFalse(Haunt.objects.filter(id=haunt_to_delete.id).exists())

    def test_delete_other_user_haunt(self):
        """Test deleting another user's haunt"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.user2_haunt.id})
        response = self.client.delete(url)

        # Should return 404 since user1 doesn't own this haunt
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify haunt still exists
        self.assertTrue(Haunt.objects.filter(id=self.user2_haunt.id).exists())

    def test_move_haunt_to_folder(self):
        """Test moving haunt to a different folder"""
        self.authenticate_user1()

        # haunt2 is currently not in any folder
        self.assertIsNone(self.haunt2.folder)

        url = reverse('haunt-move-to-folder', kwargs={'pk': self.haunt2.id})
        data = {
            'folder_id': self.folder2.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('folder', response.data)

        # Verify haunt was moved
        self.haunt2.refresh_from_db()
        self.assertEqual(self.haunt2.folder, self.folder2)

    def test_remove_haunt_from_folder(self):
        """Test removing haunt from folder"""
        self.authenticate_user1()

        # haunt1 is currently in folder1
        self.assertEqual(self.haunt1.folder, self.folder1)

        url = reverse('haunt-move-to-folder', kwargs={'pk': self.haunt1.id})
        data = {
            'folder_id': None
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['folder'])

        # Verify haunt was removed from folder
        self.haunt1.refresh_from_db()
        self.assertIsNone(self.haunt1.folder)

    def test_move_haunt_to_invalid_folder(self):
        """Test moving haunt to folder from different user"""
        self.authenticate_user1()

        # Create folder for user2
        user2_folder = Folder.objects.create(
            user=self.user2,
            name='User2 Folder'
        )

        url = reverse('haunt-move-to-folder', kwargs={'pk': self.haunt1.id})
        data = {
            'folder_id': user2_folder.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_haunts_by_folder(self):
        """Test getting haunts grouped by folder"""
        self.authenticate_user1()
        url = reverse('haunt-by-folder')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

        # Check that folder1 has haunt1
        folder1_key = str(self.folder1.id)
        self.assertIn(folder1_key, response.data)
        self.assertEqual(len(response.data[folder1_key]), 1)
        self.assertEqual(response.data[folder1_key][0]['name'], 'Test Haunt 1')

        # Check that 'null' key has haunts without folder
        self.assertIn('null', response.data)
        null_haunts = response.data['null']
        null_haunt_names = [h['name'] for h in null_haunts]
        self.assertIn('Test Haunt 2', null_haunt_names)
        self.assertIn('Public Haunt', null_haunt_names)

    def test_get_unread_counts(self):
        """Test getting unread counts for haunts and folders"""
        self.authenticate_user1()
        url = reverse('haunt-unread-counts')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('haunts', response.data)
        self.assertIn('folders', response.data)

        # Check that all user's haunts are included
        haunt_ids = list(response.data['haunts'].keys())
        self.assertIn(str(self.haunt1.id), haunt_ids)
        self.assertIn(str(self.haunt2.id), haunt_ids)
        self.assertIn(str(self.public_haunt.id), haunt_ids)

        # Check that all user's folders are included
        folder_ids = list(response.data['folders'].keys())
        self.assertIn(str(self.folder1.id), folder_ids)
        self.assertIn(str(self.folder2.id), folder_ids)

    def test_haunt_serializer_includes_folder_name(self):
        """Test that haunt serializer includes folder name"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.haunt1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['folder_name'], 'Work')

    def test_haunt_serializer_includes_display_fields(self):
        """Test that haunt serializer includes display fields"""
        self.authenticate_user1()
        url = reverse('haunt-detail', kwargs={'pk': self.haunt1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scrape_interval_display', response.data)
        self.assertIn('alert_mode_display', response.data)
        self.assertIn('is_healthy', response.data)
        self.assertIn('rss_url', response.data)

    def test_create_haunt_invalid_scrape_interval(self):
        """Test creating haunt with invalid scrape interval"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        data = {
            'name': 'Invalid Interval',
            'url': 'https://example.com/invalid',
            'scrape_interval': 45,  # Not a valid interval
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scrape_interval', response.data)

    def test_create_haunt_invalid_alert_mode(self):
        """Test creating haunt with invalid alert mode"""
        self.authenticate_user1()
        url = reverse('haunt-list')
        data = {
            'name': 'Invalid Alert Mode',
            'url': 'https://example.com/invalid',
            'alert_mode': 'invalid_mode',
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('alert_mode', response.data)
