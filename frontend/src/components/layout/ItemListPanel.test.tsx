import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ItemListPanel from './ItemListPanel';
import hauntsReducer from '../../store/slices/hauntsSlice';
import rssItemsReducer from '../../store/slices/rssItemsSlice';
import uiReducer from '../../store/slices/uiSlice';
import authReducer from '../../store/slices/authSlice';
import { RSSItem, Haunt } from '../../types';

const mockHaunt: Haunt = {
  id: '1',
  owner: 'user1',
  name: 'Test Haunt',
  url: 'https://example.com',
  description: 'Test description',
  config: {
    selectors: {},
    normalization: {},
    truthy_values: {},
  },
  current_state: {},
  last_alert_state: null,
  alert_mode: 'once',
  scrape_interval: 15,
  is_public: false,
  public_slug: null,
  folder: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockItems: RSSItem[] = [
  {
    id: '1',
    haunt: '1',
    title: 'Status Change',
    description: 'Status: Open → Closed',
    link: 'https://example.com',
    pub_date: new Date().toISOString(),
    guid: 'guid1',
  },
  {
    id: '2',
    haunt: '1',
    title: 'Another Change',
    description: 'Price changed from $10 to $15',
    link: 'https://example.com',
    pub_date: new Date(Date.now() - 3600000).toISOString(),
    guid: 'guid2',
  },
];

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      haunts: hauntsReducer,
      rssItems: rssItemsReducer,
      ui: uiReducer,
    },
    preloadedState: {
      haunts: {
        items: [mockHaunt],
        folders: [],
        selectedHaunt: mockHaunt,
        loading: false,
        error: null,
      },
      rssItems: {
        items: mockItems,
        selectedItem: null,
        unreadCounts: {},
        readStates: {},
        loading: false,
        error: null,
      },
      ui: {
        leftPanelWidth: 250,
        middlePanelWidth: 400,
        showSetupWizard: false,
        keyboardShortcutsEnabled: true,
        autoMarkReadOnScroll: false,
        collapsedFolders: [],
      },
      auth: {
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      },
      ...initialState,
    },
  });
};

describe('ItemListPanel', () => {
  it('renders empty state when no haunt is selected', () => {
    const store = createMockStore({
      haunts: {
        items: [],
        folders: [],
        selectedHaunt: null,
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    expect(screen.getByText('Select a haunt to view changes')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    const store = createMockStore({
      rssItems: {
        items: [],
        selectedItem: null,
        unreadCounts: {},
        readStates: {},
        loading: true,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    expect(screen.getByText('Loading items...')).toBeInTheDocument();
  });

  it('renders item list with items', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    expect(screen.getByText('Test Haunt')).toBeInTheDocument();
    expect(screen.getByText('Status Change')).toBeInTheDocument();
    expect(screen.getByText('Another Change')).toBeInTheDocument();
  });

  it('displays status change formatting', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    // Check that status change is parsed and displayed
    expect(screen.getByText('Status:')).toBeInTheDocument();
    expect(screen.getByText('Open')).toBeInTheDocument();
    expect(screen.getByText('Closed')).toBeInTheDocument();
  });

  it('handles item selection', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    const firstItem = screen.getByText('Status Change').closest('.item-card');
    expect(firstItem).toBeInTheDocument();
    
    if (firstItem) {
      fireEvent.click(firstItem);
      // Item should be selected (this would be verified by checking Redux state)
    }
  });

  it('displays unread indicator for unread items', () => {
    const store = createMockStore({
      rssItems: {
        items: mockItems,
        selectedItem: null,
        unreadCounts: {},
        readStates: {
          '1': {
            id: 'rs1',
            user: 'user1',
            rss_item: '1',
            is_read: false,
            is_starred: false,
          },
        },
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    const unreadIndicators = document.querySelectorAll('.unread-indicator');
    expect(unreadIndicators.length).toBeGreaterThan(0);
  });

  it('displays star indicator for starred items', () => {
    const store = createMockStore({
      rssItems: {
        items: mockItems,
        selectedItem: null,
        unreadCounts: {},
        readStates: {
          '1': {
            id: 'rs1',
            user: 'user1',
            rss_item: '1',
            is_read: true,
            is_starred: true,
          },
        },
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemListPanel />
      </Provider>
    );

    expect(screen.getByText('★')).toBeInTheDocument();
  });
});
