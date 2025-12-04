import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ItemDetailPanel from './ItemDetailPanel';
import hauntsReducer from '../../store/slices/hauntsSlice';
import rssItemsReducer from '../../store/slices/rssItemsSlice';
import uiReducer from '../../store/slices/uiSlice';
import authReducer from '../../store/slices/authSlice';
import { RSSItem } from '../../types';

const mockItem: RSSItem = {
  id: '1',
  haunt: '1',
  title: 'Test Item',
  description: 'Status: Open → Closed',
  link: 'https://example.com',
  pub_date: '2024-01-01T12:00:00Z',
  guid: 'guid1',
  ai_summary: 'The status changed from open to closed.',
};

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
        items: [],
        folders: [],
        selectedHaunt: null,
        loading: false,
        error: null,
      },
      rssItems: {
        items: [mockItem],
        selectedItem: mockItem,
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

describe('ItemDetailPanel', () => {
  it('renders empty state when no item is selected', () => {
    const store = createMockStore({
      rssItems: {
        items: [],
        selectedItem: null,
        unreadCounts: {},
        readStates: {},
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('Select an item to view details')).toBeInTheDocument();
  });

  it('renders item details', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('Test Item')).toBeInTheDocument();
    expect(screen.getByText('https://example.com')).toBeInTheDocument();
  });

  it('displays AI summary when available', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('AI Summary')).toBeInTheDocument();
    expect(screen.getByText('The status changed from open to closed.')).toBeInTheDocument();
  });

  it('displays status change formatting', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Open')).toBeInTheDocument();
    expect(screen.getByText('Closed')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('Mark Read')).toBeInTheDocument();
    expect(screen.getByText('☆')).toBeInTheDocument();
    expect(screen.getByText('Visit Site →')).toBeInTheDocument();
  });

  it('shows read button as active when item is read', () => {
    const store = createMockStore({
      rssItems: {
        items: [mockItem],
        selectedItem: mockItem,
        unreadCounts: {},
        readStates: {
          '1': {
            id: 'rs1',
            user: 'user1',
            rss_item: '1',
            is_read: true,
            is_starred: false,
          },
        },
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('✓ Read')).toBeInTheDocument();
  });

  it('shows star button as active when item is starred', () => {
    const store = createMockStore({
      rssItems: {
        items: [mockItem],
        selectedItem: mockItem,
        unreadCounts: {},
        readStates: {
          '1': {
            id: 'rs1',
            user: 'user1',
            rss_item: '1',
            is_read: false,
            is_starred: true,
          },
        },
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    expect(screen.getByText('★')).toBeInTheDocument();
  });

  it('opens link in new tab when Visit Site is clicked', () => {
    const store = createMockStore();
    const windowOpenSpy = jest.spyOn(window, 'open').mockImplementation();

    render(
      <Provider store={store}>
        <ItemDetailPanel />
      </Provider>
    );

    const visitButton = screen.getByText('Visit Site →');
    fireEvent.click(visitButton);

    expect(windowOpenSpy).toHaveBeenCalledWith(
      'https://example.com',
      '_blank',
      'noopener,noreferrer'
    );

    windowOpenSpy.mockRestore();
  });
});
