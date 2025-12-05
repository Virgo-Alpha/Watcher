import React, { useEffect, useRef, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { setSelectedItem } from '../../store/slices/rssItemsSlice';
import { markAsRead } from '../../store/slices/rssItemsSlice';
import { refreshHaunt } from '../../store/slices/hauntsSlice';
import { RSSItem } from '../../types';
import { parseStatusChange } from '../../utils/formatters';
import './ItemListPanel.css';

const ItemListPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { selectedHaunt } = useAppSelector((state) => state.haunts);
  const { items, selectedItem, readStates, loading } = useAppSelector((state) => state.rssItems);
  const { autoMarkReadOnScroll } = useAppSelector((state) => state.ui);
  
  const listContentRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const handleItemSelect = (item: RSSItem) => {
    dispatch(setSelectedItem(item));
    
    // Auto-mark as read when opened
    const readState = readStates[item.id];
    if (!readState?.is_read) {
      dispatch(markAsRead(item.id));
    }
  };

  // Auto-mark as read on scroll
  const handleIntersection = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      if (!autoMarkReadOnScroll) return;

      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.8) {
          const itemId = entry.target.getAttribute('data-item-id');
          if (itemId && !readStates[itemId]?.is_read) {
            // Delay marking as read to ensure user actually saw it
            setTimeout(() => {
              if (entry.isIntersecting) {
                dispatch(markAsRead(itemId));
              }
            }, 1000);
          }
        }
      });
    },
    [autoMarkReadOnScroll, readStates, dispatch]
  );

  // Set up intersection observer for auto-mark-as-read on scroll
  useEffect(() => {
    if (!autoMarkReadOnScroll || !listContentRef.current) return;

    observerRef.current = new IntersectionObserver(handleIntersection, {
      root: listContentRef.current,
      threshold: [0.8],
    });

    const itemElements = listContentRef.current.querySelectorAll('.item-card');
    itemElements.forEach((element) => {
      observerRef.current?.observe(element);
    });

    return () => {
      observerRef.current?.disconnect();
    };
  }, [autoMarkReadOnScroll, items, handleIntersection]);

  const isItemRead = (itemId: string): boolean => {
    return readStates[itemId]?.is_read || false;
  };

  const isItemStarred = (itemId: string): boolean => {
    return readStates[itemId]?.is_starred || false;
  };

  const formatTimeSince = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
  };



  if (!selectedHaunt) {
    return (
      <div className="item-list-panel-container">
        <div className="empty-state">
          <p>Select a haunt to view changes</p>
        </div>
      </div>
    );
  }

  const handleRefresh = async () => {
    if (selectedHaunt && !isRefreshing) {
      setIsRefreshing(true);
      try {
        await dispatch(refreshHaunt(selectedHaunt.id)).unwrap();
        console.log('Refresh initiated successfully');
      } catch (error: any) {
        console.error('Refresh failed:', error);
        if (error?.status === 429) {
          alert('Please wait a few minutes before refreshing again.');
        } else {
          alert('Failed to refresh. Please try again.');
        }
      } finally {
        setTimeout(() => setIsRefreshing(false), 1000);
      }
    }
  };

  const formatLastScraped = (dateString: string | null): string => {
    if (!dateString) return 'Never scraped';
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'Scraped just now';
    if (seconds < 3600) return `Scraped ${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `Scraped ${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `Scraped ${Math.floor(seconds / 86400)}d ago`;
    return `Scraped on ${date.toLocaleDateString()}`;
  };

  return (
    <div className="item-list-panel-container">
      <div className="item-list-header">
        <div className="header-left">
          <h3>{selectedHaunt.name}</h3>
          <span className="item-count">{items.length} items</span>
        </div>
        <button 
          className={`refresh-button ${isRefreshing ? 'refreshing' : ''}`}
          onClick={handleRefresh}
          disabled={isRefreshing}
          title={isRefreshing ? "Refreshing..." : "Refresh (R)"}
          aria-label={isRefreshing ? "Refreshing haunt" : "Refresh haunt"}
        >
          ↻
        </button>
      </div>
      {selectedHaunt.last_scraped_at && (
        <div className="haunt-metadata">
          <span className="last-scraped">{formatLastScraped(selectedHaunt.last_scraped_at)}</span>
        </div>
      )}

      <div className="item-list-content" ref={listContentRef}>
        {items.length === 0 ? (
          <div className="empty-state">
            <p>No changes detected yet</p>
            <p className="empty-state-hint">Changes will appear here when detected</p>
          </div>
        ) : (
          items.map(item => (
            <div
              key={item.id}
              data-item-id={item.id}
              className={`item-card ${selectedItem?.id === item.id ? 'selected' : ''} ${
                isItemRead(item.id) ? 'read' : 'unread'
              }`}
              onClick={() => handleItemSelect(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleItemSelect(item);
                }
              }}
              aria-label={`${item.title} - ${isItemRead(item.id) ? 'read' : 'unread'}${isItemStarred(item.id) ? ', starred' : ''}`}
            >
              <div className="item-card-header">
                <div className="item-status-indicators">
                  {!isItemRead(item.id) && <span className="unread-indicator" />}
                  {isItemStarred(item.id) && <span className="star-indicator">★</span>}
                </div>
                <span className="item-time">{formatTimeSince(item.pub_date)}</span>
              </div>
              
              <div className="item-card-title">{item.title}</div>
              
              <div className="item-card-description">
                {(() => {
                  const statusChange = parseStatusChange(item.description);
                  if (statusChange) {
                    return (
                      <span className="status-change">
                        <span className="status-key">{statusChange.key}:</span>{' '}
                        <span className="status-old">{statusChange.oldValue}</span>
                        {' → '}
                        <span className="status-new">{statusChange.newValue}</span>
                      </span>
                    );
                  }
                  return item.description;
                })()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ItemListPanel;
