"""
Tests for folder management API endpoints.
"""
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Folder, Haunt, UserUIPreferences

User = get_user_model()


class FolderAPITestCase(TestCase):
    """Test case for folder management API"""
    
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
        
        # Create test folders for user1
        self.root_folder = Folder.objects.create(
            user=self.user1,
            name='Work'
        )
        self.child_folder = Folder.objects.create(
            user=self.user1,
            name='Projects',
            parent=self.root_folder
        )
        self.other_folder = Folder.objects.create(
            user=self.user1,
            name='Personal'
        )
        
        # Create folder for user2
        self.user2_folder = Folder.objects.create(
            user=self.user2,
            name='User2 Folder'
        )
        
        # Create test haunts
        self.haunt1 = Haunt.objects.create(
            owner=self.user1,
            name='Test Haunt 1',
            url='https://example.com/1',
            folder=self.root_folder
        )
        self.haunt2 = Haunt.objects.create(
            owner=self.user1,
            name='Test Haunt 2',
            url='https://example.com/2'
        )
    
    def authenticate_user1(self):
        """Authenticate as user1"""
        self.client.force_authenticate(user=self.user1)
    
    def authenticate_user2(self):
        """Authenticate as user2"""
        self.client.force_authenticate(user=self.user2)
    
    def test_list_folders_authenticated(self):
        """Test listing folders for authenticated user"""
        self.authenticate_user1()
        url = reverse('folder-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 3 folders for user1
        
        # Check folder names
        folder_names = [folder['name'] for folder in response.data]
        self.assertIn('Work', folder_names)
        self.assertIn('Projects', folder_names)
        self.assertIn('Personal', folder_names)
    
    def test_list_folders_unauthenticated(self):
        """Test listing folders without authentication"""
        url = reverse('folder-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_folders_user_isolation(self):
        """Test that users only see their own folders"""
        self.authenticate_user2()
        url = reverse('folder-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only 1 folder for user2
        self.assertEqual(response.data[0]['name'], 'User2 Folder')
    
    def test_create_folder(self):
        """Test creating a new folder"""
        self.authenticate_user1()
        url = reverse('folder-list')
        data = {
            'name': 'New Folder'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Folder')
        self.assertIsNone(response.data['parent'])
        
        # Verify folder was created in database
        folder = Folder.objects.get(id=response.data['id'])
        self.assertEqual(folder.user, self.user1)
        self.assertEqual(folder.name, 'New Folder')
    
    def test_create_folder_with_parent(self):
        """Test creating a folder with a parent"""
        self.authenticate_user1()
        url = reverse('folder-list')
        data = {
            'name': 'Sub Folder',
            'parent': self.root_folder.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Sub Folder')
        self.assertEqual(response.data['parent'], self.root_folder.id)
        self.assertEqual(response.data['depth'], 1)
    
    def test_create_folder_invalid_parent(self):
        """Test creating folder with parent from different user"""
        self.authenticate_user1()
        url = reverse('folder-list')
        data = {
            'name': 'Invalid Folder',
            'parent': self.user2_folder.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)
    
    def test_update_folder(self):
        """Test updating a folder"""
        self.authenticate_user1()
        url = reverse('folder-detail', kwargs={'pk': self.root_folder.id})
        data = {
            'name': 'Updated Work'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Work')
        
        # Verify in database
        self.root_folder.refresh_from_db()
        self.assertEqual(self.root_folder.name, 'Updated Work')
    
    def test_delete_folder(self):
        """Test deleting a folder"""
        self.authenticate_user1()
        
        # Create a folder to delete
        folder_to_delete = Folder.objects.create(
            user=self.user1,
            name='To Delete'
        )
        
        url = reverse('folder-detail', kwargs={'pk': folder_to_delete.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify folder was deleted
        self.assertFalse(Folder.objects.filter(id=folder_to_delete.id).exists())
    
    def test_delete_folder_with_haunts(self):
        """Test deleting folder moves haunts to parent"""
        self.authenticate_user1()
        
        # Verify haunt is in root_folder initially
        self.assertEqual(self.haunt1.folder, self.root_folder)
        
        url = reverse('folder-detail', kwargs={'pk': self.root_folder.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify haunt folder was set to None (no parent)
        self.haunt1.refresh_from_db()
        self.assertIsNone(self.haunt1.folder)
    
    def test_folder_tree(self):
        """Test getting folder tree structure"""
        self.authenticate_user1()
        url = reverse('folder-tree')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only root folders with nested children
        root_folders = [f for f in response.data if f['parent'] is None]
        self.assertEqual(len(root_folders), 2)  # Work and Personal
        
        # Find Work folder and check it has children
        work_folder = next(f for f in root_folders if f['name'] == 'Work')
        self.assertEqual(len(work_folder['children']), 1)
        self.assertEqual(work_folder['children'][0]['name'], 'Projects')
    
    def test_assign_haunts_to_folder(self):
        """Test assigning haunts to a folder"""
        self.authenticate_user1()
        
        # haunt2 is currently not in any folder
        self.assertIsNone(self.haunt2.folder)
        
        url = reverse('folder-assign-haunts', kwargs={'pk': self.other_folder.id})
        data = {
            'haunt_ids': [str(self.haunt2.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_count'], 1)
        
        # Verify haunt was assigned
        self.haunt2.refresh_from_db()
        self.assertEqual(self.haunt2.folder, self.other_folder)
    
    def test_assign_haunts_invalid_haunt(self):
        """Test assigning non-existent or other user's haunt"""
        self.authenticate_user1()
        
        # Create haunt for user2
        user2_haunt = Haunt.objects.create(
            owner=self.user2,
            name='User2 Haunt',
            url='https://example.com/user2'
        )
        
        url = reverse('folder-assign-haunts', kwargs={'pk': self.other_folder.id})
        data = {
            'haunt_ids': [str(user2_haunt.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not found or not owned', response.data['error'])
    
    def test_unassign_haunts_from_folder(self):
        """Test unassigning haunts from a folder"""
        self.authenticate_user1()
        
        # Refresh haunt1 from database to get current state
        self.haunt1.refresh_from_db()
        
        # haunt1 is currently in root_folder
        self.assertEqual(self.haunt1.folder, self.root_folder)
        
        url = reverse('folder-unassign-haunts', kwargs={'pk': self.root_folder.id})
        data = {
            'haunt_ids': [str(self.haunt1.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unassigned_count'], 1)
        
        # Verify haunt was unassigned
        self.haunt1.refresh_from_db()
        self.assertIsNone(self.haunt1.folder)
    
    def test_folder_haunt_count(self):
        """Test folder haunt count calculation"""
        self.authenticate_user1()
        url = reverse('folder-detail', kwargs={'pk': self.root_folder.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['haunt_count'], 1)  # haunt1 is in root_folder


class UserUIPreferencesAPITestCase(TestCase):
    """Test case for user UI preferences API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='user@example.com',
            password='testpass123'
        )
        
        # Create a folder for testing
        self.folder = Folder.objects.create(
            user=self.user,
            name='Test Folder'
        )
    
    def authenticate(self):
        """Authenticate user"""
        self.client.force_authenticate(user=self.user)
    
    def test_get_preferences_creates_default(self):
        """Test getting preferences creates default if none exist"""
        self.authenticate()
        url = reverse('preferences-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['left_panel_width'], 250)  # default value
        self.assertEqual(response.data['keyboard_shortcuts_enabled'], True)
        
        # Verify preferences were created in database
        self.assertTrue(UserUIPreferences.objects.filter(user=self.user).exists())
    
    def test_update_preferences(self):
        """Test updating user preferences"""
        self.authenticate()
        
        # First get preferences to create them
        list_url = reverse('preferences-list')
        self.client.get(list_url)
        
        # Get the preferences object
        preferences = UserUIPreferences.objects.get(user=self.user)
        
        # Update preferences
        update_url = reverse('preferences-detail', kwargs={'pk': preferences.id})
        data = {
            'left_panel_width': 300,
            'keyboard_shortcuts_enabled': False,
            'auto_mark_read_on_scroll': True
        }
        response = self.client.patch(update_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['left_panel_width'], 300)
        self.assertEqual(response.data['keyboard_shortcuts_enabled'], False)
        self.assertEqual(response.data['auto_mark_read_on_scroll'], True)
    
    def test_toggle_folder_collapsed(self):
        """Test toggling folder collapsed state"""
        self.authenticate()
        
        url = reverse('preferences-toggle-folder-collapsed')
        data = {
            'folder_id': self.folder.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_collapsed'])
        
        # Toggle again
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_collapsed'])
    
    def test_toggle_folder_collapsed_invalid_folder(self):
        """Test toggling collapsed state for non-existent folder"""
        self.authenticate()
        
        url = reverse('preferences-toggle-folder-collapsed')
        data = {
            'folder_id': 99999  # Non-existent folder
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_reset_preferences(self):
        """Test resetting preferences to defaults"""
        self.authenticate()
        
        # First create and modify preferences
        list_url = reverse('preferences-list')
        self.client.get(list_url)
        
        preferences = UserUIPreferences.objects.get(user=self.user)
        preferences.left_panel_width = 400
        preferences.save()
        
        # Reset preferences
        delete_url = reverse('preferences-detail', kwargs={'pk': preferences.id})
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['left_panel_width'], 250)  # back to default
    
    def test_preferences_user_isolation(self):
        """Test that users can only access their own preferences"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create preferences for other user
        other_preferences = UserUIPreferences.objects.create(
            user=other_user,
            left_panel_width=500
        )
        
        # Authenticate as first user
        self.authenticate()
        
        # Try to access other user's preferences
        url = reverse('preferences-detail', kwargs={'pk': other_preferences.id})
        response = self.client.get(url)
        
        # Should return current user's preferences, not other user's
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['left_panel_width'], 250)  # default, not 500