import React from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { markAsRead, markAsUnread, toggleStar } from '../../store/slices/rssItemsSlice';
import { parseStatusChanges } from '../../utils/formatters';
import './ItemDetailPanel.css';

const ItemDetailPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { selectedItem, readStates } = useAppSelector((state) => state.rssItems);

  if (!selectedItem) {
    return (
      <div className="item-detail-panel-container">
        <div className="empty-state">
          <p>Select an item to view details</p>
        </div>
      </div>
    );
  }

  const readState = readStates[selectedItem.id];
  const isRead = readState?.is_read || false;
  const isStarred = readState?.is_starred || false;

  const handleToggleRead = () => {
    if (isRead) {
      dispatch(markAsUnread(selectedItem.id));
    } else {
      dispatch(markAsRead(selectedItem.id));
    }
  };

  const handleToggleStar = () => {
    dispatch(toggleStar(selectedItem.id));
  };

  const handleVisitSite = () => {
    window.open(selectedItem.link, '_blank', 'noopener,noreferrer');
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="item-detail-panel-container">
      <div className="item-detail-header">
        <h2 className="item-detail-title">{selectedItem.title}</h2>
        
        <div className="item-detail-actions">
          <button
            className={`action-button ${isRead ? 'active' : ''}`}
            onClick={handleToggleRead}
            title={isRead ? 'Mark as unread' : 'Mark as read'}
          >
            {isRead ? '✓ Read' : 'Mark Read'}
          </button>
          
          <button
            className={`action-button star-button ${isStarred ? 'active' : ''}`}
            onClick={handleToggleStar}
            title={isStarred ? 'Unstar' : 'Star'}
          >
            {isStarred ? '★' : '☆'}
          </button>
          
          <button
            className="action-button primary"
            onClick={handleVisitSite}
            title="Visit site"
          >
            Visit Site →
          </button>
        </div>
      </div>

      <div className="item-detail-meta">
        <span className="item-detail-date">{formatDate(selectedItem.pub_date)}</span>
      </div>

      <div className="item-detail-content">
        {selectedItem.ai_summary && (
          <div className="ai-summary-section">
            <h3 className="section-title">AI Summary</h3>
            <div className="ai-summary-content">
              {selectedItem.ai_summary}
            </div>
          </div>
        )}

        <div className="change-description-section">
          <h3 className="section-title">Change Details</h3>
          <div className="change-description-content">
            {(() => {
              const statusChanges = parseStatusChanges(selectedItem.description);
              if (statusChanges.length > 0) {
                return (
                  <div className="status-changes-list">
                    {statusChanges.map((change, index) => (
                      <div key={index} className="status-change-item">
                        <div className="status-change-key">{change.key}</div>
                        <div className="status-change-values">
                          <span className="status-change-old">{change.oldValue}</span>
                          <span className="status-change-arrow">→</span>
                          <span className="status-change-new">{change.newValue}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                );
              }
              return <div className="description-text">{selectedItem.description}</div>;
            })()}
          </div>
        </div>

        <div className="item-link-section">
          <h3 className="section-title">Source</h3>
          <a 
            href={selectedItem.link} 
            target="_blank" 
            rel="noopener noreferrer"
            className="item-link"
          >
            {selectedItem.link}
          </a>
        </div>
      </div>
    </div>
  );
};

export default ItemDetailPanel;
