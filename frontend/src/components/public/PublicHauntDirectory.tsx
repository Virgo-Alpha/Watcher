import React, { useEffect, useState } from 'react';
import { Haunt, Subscription } from '../../types';
import apiClient from '../../services/api';
import './PublicHauntDirectory.css';

const PublicHauntDirectory: React.FC = () => {
  const [publicHaunts, setPublicHaunts] = useState<Haunt[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [haunts, subs] = await Promise.all([
        apiClient.getPublicHaunts(),
        apiClient.getSubscriptions(),
      ]);
      setPublicHaunts(haunts);
      setSubscriptions(subs);
    } catch (err: any) {
      setError(err.message || 'Failed to load public haunts');
    } finally {
      setLoading(false);
    }
  };

  const isSubscribed = (hauntId: string): boolean => {
    return subscriptions.some(sub => sub.haunt === hauntId);
  };

  const handleSubscribe = async (hauntId: string) => {
    try {
      const subscription = await apiClient.subscribe(hauntId);
      setSubscriptions([...subscriptions, subscription]);
    } catch (err: any) {
      alert(err.message || 'Failed to subscribe');
    }
  };

  const handleUnsubscribe = async (hauntId: string) => {
    const subscription = subscriptions.find(sub => sub.haunt === hauntId);
    if (!subscription) return;

    try {
      await apiClient.unsubscribe(subscription.id);
      setSubscriptions(subscriptions.filter(sub => sub.id !== subscription.id));
    } catch (err: any) {
      alert(err.message || 'Failed to unsubscribe');
    }
  };

  const filteredHaunts = publicHaunts.filter(haunt =>
    haunt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    haunt.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    haunt.url.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="public-directory-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading public haunts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="public-directory-container">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={loadData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="public-directory-container">
      <div className="directory-header">
        <h2>Public Haunt Directory</h2>
        <p className="directory-description">
          Discover and subscribe to haunts shared by the community
        </p>
      </div>

      <div className="directory-search">
        <input
          type="text"
          className="search-input"
          placeholder="Search haunts by name, description, or URL..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="directory-content">
        {filteredHaunts.length === 0 ? (
          <div className="empty-state">
            {searchQuery ? (
              <p>No haunts match your search</p>
            ) : (
              <p>No public haunts available yet</p>
            )}
          </div>
        ) : (
          <div className="haunts-grid">
            {filteredHaunts.map(haunt => (
              <div key={haunt.id} className="haunt-card">
                <div className="haunt-card-header">
                  <h3 className="haunt-card-title">{haunt.name}</h3>
                  {haunt.unread_count !== undefined && haunt.unread_count > 0 && (
                    <span className="unread-badge">{haunt.unread_count}</span>
                  )}
                </div>

                <p className="haunt-card-description">{haunt.description}</p>

                <div className="haunt-card-meta">
                  <span className="haunt-url" title={haunt.url}>
                    {new URL(haunt.url).hostname}
                  </span>
                  <span className="haunt-interval">
                    Checks every {haunt.scrape_interval < 60 
                      ? `${haunt.scrape_interval}m` 
                      : haunt.scrape_interval === 60 
                      ? '1h' 
                      : `${Math.floor(haunt.scrape_interval / 60)}h`}
                  </span>
                </div>

                <div className="haunt-card-actions">
                  {isSubscribed(haunt.id) ? (
                    <button
                      className="action-button subscribed"
                      onClick={() => handleUnsubscribe(haunt.id)}
                    >
                      ✓ Subscribed
                    </button>
                  ) : (
                    <button
                      className="action-button subscribe"
                      onClick={() => handleSubscribe(haunt.id)}
                    >
                      Subscribe
                    </button>
                  )}
                  <a
                    href={haunt.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="action-button secondary"
                  >
                    Visit Site
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PublicHauntDirectory;
