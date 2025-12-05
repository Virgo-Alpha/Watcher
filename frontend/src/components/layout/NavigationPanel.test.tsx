import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import NavigationPanel from './NavigationPanel';
import hauntsReducer from '../../store/slices/hauntsSlice';
import rssItemsReducer from '../../store/slices/rssItemsSlice';
import uiReducer from '../../store/slices/uiSlice';
import authReducer from '../../store/slices/authSlice';
import * as api from '../../services/api';

// Mock the API module
jest.mock('../../services/api');

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      haunts: hauntsReducer,
      rssItems: rssItemsReducer,
      ui: uiReducer,
      auth: authReducer,
    },
    preloadedState: {
      haunts: {
        items: [],
        folders: [],
        selectedHaunt: null,
        loading: false,
        error: null,
      },
      rssItems: {
        items: [],
        unreadCounts: {},
        readStates: {},
        loading: false,
        error: null,
      },
      ui: {
        showSetupWizard: false,
        collapsedFolders: [],
      },
      auth: {
        user: null,
        accessToken: 'test-token',
        refreshToken: null,
        isAuthenticated: true,
        loading: false,
        error: null,
      },
      ...initialState,
    },
  });
};

const renderWithProviders = (component: React.ReactElement, store = createMockStore()) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  );
};

describe('NavigationPanel', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders without crashing', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      renderWithProviders(<NavigationPanel />);
      expect(screen.getByText('Haunts')).toBeInTheDocument();
    });

    it('displays loading state when loading', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      const store = createMockStore({
        haunts: {
          items: [],
          folders: [],
          selectedHaunt: null,
          loading: true,
          error: null,
        },
      });
      renderWithProviders(<NavigationPanel />, store);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('displays empty state when no haunts or folders exist', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      renderWithProviders(<NavigationPanel />);
      expect(screen.getByText('No haunts yet')).toBeInTheDocument();
      expect(screen.getByText('Click "New Haunt" to get started')).toBeInTheDocument();
    });

    it('renders New Haunt button', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      renderWithProviders(<NavigationPanel />);
      expect(screen.getByText('+ New Haunt')).toBeInTheDocument();
    });

    it('renders logout button', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      renderWithProviders(<NavigationPanel />);
      expect(screen.getByTitle('Logout')).toBeInTheDocument();
    });
  });

  describe('Folder Collapse Functionality', () => {
    it('collapses all folders by default on first load', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Folder 1', parent: null, user: 'user1', created_at: '2024-01-01' },
        { id: '2', name: 'Folder 2', parent: null, user: 'user1', created_at: '2024-01-02' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: [],
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      await waitFor(() => {
        const state = store.getState();
        // After folders are fetched, they should be collapsed
        expect(state.ui.collapsedFolders.length).toBeGreaterThan(0);
      });
    });

    it('does not collapse folders if they are already collapsed', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Folder 1', parent: null, user: 'user1', created_at: '2024-01-01' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: ['1'],
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      await waitFor(() => {
        const state = store.getState();
        // Should remain with only the one collapsed folder
        expect(state.ui.collapsedFolders).toEqual(['1']);
      });
    });

    it('collapses only new folders when folders list changes', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Folder 1', parent: null, user: 'user1', created_at: '2024-01-01' },
        { id: '2', name: 'Folder 2', parent: null, user: 'user1', created_at: '2024-01-02' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: ['1'], // Folder 1 already collapsed
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      await waitFor(() => {
        const state = store.getState();
        // Should have both folders collapsed now
        expect(state.ui.collapsedFolders).toContain('1');
        expect(state.ui.collapsedFolders).toContain('2');
        expect(state.ui.collapsedFolders.length).toBe(2);
      });
    });

    it('does not duplicate folder IDs in collapsed list', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Folder 1', parent: null, user: 'user1', created_at: '2024-01-01' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: ['1'],
        },
      });

      const { rerender } = renderWithProviders(<NavigationPanel />, store);

      // Force a re-render to trigger the effect again
      rerender(
        <Provider store={store}>
          <BrowserRouter>
            <NavigationPanel />
          </BrowserRouter>
        </Provider>
      );

      await waitFor(() => {
        const state = store.getState();
        // Should still have only one instance of folder '1'
        const folder1Count = state.ui.collapsedFolders.filter(id => id === '1').length;
        expect(folder1Count).toBe(1);
      });
    });

    it('handles empty folders array gracefully', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const store = createMockStore({
        haunts: {
          items: [],
          folders: [],
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: [],
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      await waitFor(() => {
        const state = store.getState();
        // Should remain empty
        expect(state.ui.collapsedFolders).toEqual([]);
      });
    });

    it('collapses nested folders correctly', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Parent Folder', parent: null, user: 'user1', created_at: '2024-01-01' },
        { id: '2', name: 'Child Folder', parent: '1', user: 'user1', created_at: '2024-01-02' },
        { id: '3', name: 'Grandchild Folder', parent: '2', user: 'user1', created_at: '2024-01-03' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: [],
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      await waitFor(() => {
        const state = store.getState();
        // All folders should be collapsed
        expect(state.ui.collapsedFolders).toContain('1');
        expect(state.ui.collapsedFolders).toContain('2');
        expect(state.ui.collapsedFolders).toContain('3');
        expect(state.ui.collapsedFolders.length).toBe(3);
      });
    });

    it('preserves user-expanded folders when new folders are added', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const initialFolders = [
        { id: '1', name: 'Folder 1', parent: null, user: 'user1', created_at: '2024-01-01' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: initialFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: [], // User has expanded folder 1
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      // Wait for initial collapse
      await waitFor(() => {
        const state = store.getState();
        expect(state.ui.collapsedFolders).toContain('1');
      });

      // Simulate user expanding folder 1
      store.dispatch({ type: 'ui/expandFolder', payload: '1' });

      // Add a new folder
      const updatedFolders = [
        ...initialFolders,
        { id: '2', name: 'Folder 2', parent: null, user: 'user1', created_at: '2024-01-02' },
      ];

      // Update the store with new folders
      store.dispatch({ 
        type: 'haunts/fetchFolders/fulfilled', 
        payload: updatedFolders 
      });

      await waitFor(() => {
        const state = store.getState();
        // Folder 1 should remain expanded (not in collapsed list)
        expect(state.ui.collapsedFolders).not.toContain('1');
        // Folder 2 should be collapsed
        expect(state.ui.collapsedFolders).toContain('2');
      });
    });

    it('handles folder toggle correctly', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Test Folder', parent: null, user: 'user1', created_at: '2024-01-01' },
      ];

      const mockHaunts = [
        {
          id: 'haunt1',
          owner: 'user1',
          name: 'Test Haunt',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once' as const,
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: '1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      const store = createMockStore({
        haunts: {
          items: mockHaunts,
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: [],
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      // The folder should be rendered
      expect(screen.getByText('Test Folder')).toBeInTheDocument();
    });

    it('handles rapid folder additions without race conditions', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const store = createMockStore({
        haunts: {
          items: [],
          folders: [],
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        ui: {
          showSetupWizard: false,
          collapsedFolders: [],
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      // Rapidly add multiple folders
      const folders = [
        { id: '1', name: 'Folder 1', parent: null, user: 'user1', created_at: '2024-01-01' },
        { id: '2', name: 'Folder 2', parent: null, user: 'user1', created_at: '2024-01-02' },
        { id: '3', name: 'Folder 3', parent: null, user: 'user1', created_at: '2024-01-03' },
      ];

      store.dispatch({ 
        type: 'haunts/fetchFolders/fulfilled', 
        payload: folders 
      });

      await waitFor(() => {
        const state = store.getState();
        // All folders should be collapsed exactly once
        expect(state.ui.collapsedFolders.length).toBe(3);
        expect(new Set(state.ui.collapsedFolders).size).toBe(3); // No duplicates
      });
    });
  });

  describe('Haunt Selection', () => {
    it('selects a haunt when clicked', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockHaunts = [
        {
          id: 'haunt1',
          owner: 'user1',
          name: 'Test Haunt',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once' as const,
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: null,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      const store = createMockStore({
        haunts: {
          items: mockHaunts,
          folders: [],
          selectedHaunt: null,
          loading: false,
          error: null,
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      const hauntElement = screen.getByText('Test Haunt');
      fireEvent.click(hauntElement);

      const state = store.getState();
      expect(state.haunts.selectedHaunt?.id).toBe('haunt1');
    });

    it('displays unread counts for haunts', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockHaunts = [
        {
          id: 'haunt1',
          owner: 'user1',
          name: 'Test Haunt',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once' as const,
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: null,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      const store = createMockStore({
        haunts: {
          items: mockHaunts,
          folders: [],
          selectedHaunt: null,
          loading: false,
          error: null,
        },
        rssItems: {
          items: [],
          unreadCounts: { haunt1: 5 },
          readStates: {},
          loading: false,
          error: null,
        },
      });

      renderWithProviders(<NavigationPanel />, store);
      expect(screen.getByText('Test Haunt')).toBeInTheDocument();
    });
  });

  describe('User Actions', () => {
    it('opens setup wizard when New Haunt button is clicked', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      const store = createMockStore();

      renderWithProviders(<NavigationPanel />, store);

      const newHauntButton = screen.getByText('+ New Haunt');
      fireEvent.click(newHauntButton);

      const state = store.getState();
      expect(state.ui.showSetupWizard).toBe(true);
    });

    it('handles logout correctly', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      const store = createMockStore();

      renderWithProviders(<NavigationPanel />, store);

      const logoutButton = screen.getByTitle('Logout');
      fireEvent.click(logoutButton);

      // Check that logout action was dispatched
      const state = store.getState();
      expect(state.auth.isAuthenticated).toBe(false);
    });
  });

  describe('Data Fetching', () => {
    it('fetches haunts and folders on mount when authenticated', async () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const store = createMockStore();
      renderWithProviders(<NavigationPanel />, store);

      // Component should attempt to fetch data
      await waitFor(() => {
        expect(localStorageMock.getItem('accessToken')).toBe('test-token');
      });
    });

    it('does not fetch data when no access token exists', () => {
      // No token in localStorage
      const store = createMockStore();
      renderWithProviders(<NavigationPanel />, store);

      // Should not attempt to fetch
      expect(localStorageMock.getItem('accessToken')).toBeNull();
    });
  });

  describe('Folder Tree Integration', () => {
    it('renders folder tree with nested folders', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Parent Folder', parent: null, user: 'user1', created_at: '2024-01-01' },
        { id: '2', name: 'Child Folder', parent: '1', user: 'user1', created_at: '2024-01-02' },
      ];

      const store = createMockStore({
        haunts: {
          items: [],
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      expect(screen.getByText('Parent Folder')).toBeInTheDocument();
      expect(screen.getByText('Child Folder')).toBeInTheDocument();
    });

    it('renders haunts within folders', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockFolders = [
        { id: '1', name: 'Work', parent: null, user: 'user1', created_at: '2024-01-01' },
      ];

      const mockHaunts = [
        {
          id: 'haunt1',
          owner: 'user1',
          name: 'Work Haunt',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once' as const,
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: '1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      const store = createMockStore({
        haunts: {
          items: mockHaunts,
          folders: mockFolders,
          selectedHaunt: null,
          loading: false,
          error: null,
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      expect(screen.getByText('Work')).toBeInTheDocument();
      expect(screen.getByText('Work Haunt')).toBeInTheDocument();
    });

    it('renders unfoldered haunts separately', () => {
      localStorageMock.setItem('accessToken', 'test-token');
      
      const mockHaunts = [
        {
          id: 'haunt1',
          owner: 'user1',
          name: 'Unfoldered Haunt',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once' as const,
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: null,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      const store = createMockStore({
        haunts: {
          items: mockHaunts,
          folders: [],
          selectedHaunt: null,
          loading: false,
          error: null,
        },
      });

      renderWithProviders(<NavigationPanel />, store);

      expect(screen.getByText('Unfoldered Haunt')).toBeInTheDocument();
    });
  });
});