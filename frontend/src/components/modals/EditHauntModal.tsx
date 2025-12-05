import React, { useState, useEffect } from 'react';
import { Haunt } from '../../types';
import './EditHauntModal.css';

interface EditHauntModalProps {
  haunt: Haunt;
  onSave: (id: string, data: Partial<Haunt>) => void;
  onClose: () => void;
}

const EditHauntModal: React.FC<EditHauntModalProps> = ({ haunt, onSave, onClose }) => {
  const [name, setName] = useState(haunt.name);
  const [url, setUrl] = useState(haunt.url);
  const [description, setDescription] = useState(haunt.description || '');
  const [scrapeInterval, setScrapeInterval] = useState(haunt.scrape_interval);
  const [isActive, setIsActive] = useState(haunt.is_active);
  const [enableAiSummary, setEnableAiSummary] = useState(haunt.enable_ai_summary);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      await onSave(haunt.id, {
        name: name.trim(),
        url: url.trim(),
        description: description.trim(),
        scrape_interval: scrapeInterval,
        is_active: isActive,
        enable_ai_summary: enableAiSummary,
      });
      onClose();
    } catch (error) {
      console.error('Failed to update haunt:', error);
      setSaving(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content edit-haunt-modal">
        <div className="modal-header">
          <h2>Edit Haunt</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label htmlFor="name">Name *</label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                maxLength={200}
                placeholder="My Haunt"
              />
            </div>

            <div className="form-group">
              <label htmlFor="url">URL *</label>
              <input
                id="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                placeholder="https://example.com"
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="What are you monitoring?"
              />
            </div>

            <div className="form-group">
              <label htmlFor="scrapeInterval">Check Interval</label>
              <select
                id="scrapeInterval"
                value={scrapeInterval}
                onChange={(e) => setScrapeInterval(Number(e.target.value))}
              >
                <option value={15}>Every 15 minutes</option>
                <option value={30}>Every 30 minutes</option>
                <option value={60}>Every hour</option>
                <option value={360}>Every 6 hours</option>
                <option value={1440}>Daily</option>
              </select>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                />
                <span>Active (monitoring enabled)</span>
              </label>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={enableAiSummary}
                  onChange={(e) => setEnableAiSummary(e.target.checked)}
                />
                <span>Enable AI summaries</span>
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditHauntModal;
