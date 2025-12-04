import React, { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import {
  setKeyboardShortcutsEnabled,
  setAutoMarkReadOnScroll,
  updateUserPreferences,
} from '../../store/slices/uiSlice';
import './UserPreferences.css';

const UserPreferences: React.FC = () => {
  const dispatch = useAppDispatch();
  const { keyboardShortcutsEnabled, autoMarkReadOnScroll } = useAppSelector((state) => state.ui);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const handleToggleKeyboardShortcuts = async (enabled: boolean) => {
    dispatch(setKeyboardShortcutsEnabled(enabled));
    await savePreference({ keyboard_shortcuts_enabled: enabled });
  };

  const handleToggleAutoMarkRead = async (enabled: boolean) => {
    dispatch(setAutoMarkReadOnScroll(enabled));
    await savePreference({ auto_mark_read_on_scroll: enabled });
  };

  const savePreference = async (data: any) => {
    setSaving(true);
    setSaveMessage(null);
    try {
      await dispatch(updateUserPreferences(data)).unwrap();
      setSaveMessage('Saved successfully');
      setTimeout(() => setSaveMessage(null), 2000);
    } catch (err: any) {
      setSaveMessage('Failed to save');
      setTimeout(() => setSaveMessage(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="user-preferences-container">
      <div className="preferences-header">
        <h2>User Preferences</h2>
        <p className="preferences-description">
          Customize your reading experience
        </p>
      </div>

      {saveMessage && (
        <div className={`save-message ${saveMessage.includes('Failed') ? 'error' : 'success'}`}>
          {saveMessage}
        </div>
      )}

      <div className="preferences-content">
        <div className="preference-section">
          <h3>Reading Behavior</h3>
          
          <div className="preference-item">
            <div className="preference-info">
              <label htmlFor="auto-mark-read" className="preference-label">
                Auto-mark as read on scroll
              </label>
              <p className="preference-description">
                Automatically mark items as read when you scroll past them
              </p>
            </div>
            <label className="toggle-switch">
              <input
                id="auto-mark-read"
                type="checkbox"
                checked={autoMarkReadOnScroll}
                onChange={(e) => handleToggleAutoMarkRead(e.target.checked)}
                disabled={saving}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div className="preference-section">
          <h3>Keyboard Shortcuts</h3>
          
          <div className="preference-item">
            <div className="preference-info">
              <label htmlFor="keyboard-shortcuts" className="preference-label">
                Enable keyboard shortcuts
              </label>
              <p className="preference-description">
                Use J/K for navigation, M for read/unread, S for star, and more
              </p>
            </div>
            <label className="toggle-switch">
              <input
                id="keyboard-shortcuts"
                type="checkbox"
                checked={keyboardShortcutsEnabled}
                onChange={(e) => handleToggleKeyboardShortcuts(e.target.checked)}
                disabled={saving}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div className="keyboard-shortcuts-info">
            <p className="info-text">
              Press <kbd>?</kbd> to view all available keyboard shortcuts
            </p>
          </div>
        </div>

        <div className="preference-section">
          <h3>About</h3>
          <div className="about-info">
            <p>
              Watcher is a site change monitoring application that "haunts" websites to detect
              user-defined changes and provides RSS feeds with a Google Reader-style interface.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserPreferences;
