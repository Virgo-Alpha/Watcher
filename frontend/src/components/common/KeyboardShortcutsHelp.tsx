import React from 'react';
import { KEYBOARD_SHORTCUTS } from '../../services/keyboardShortcuts';
import './KeyboardShortcutsHelp.css';

interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="shortcuts-overlay" onClick={onClose}>
      <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="shortcuts-header">
          <h2>Keyboard Shortcuts</h2>
          <button className="close-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="shortcuts-content">
          <div className="shortcuts-section">
            <h3>Navigation</h3>
            <div className="shortcuts-list">
              {KEYBOARD_SHORTCUTS.filter(s => 
                ['nextItem', 'previousItem'].includes(s.action)
              ).map(shortcut => (
                <div key={shortcut.key} className="shortcut-item">
                  <kbd className="shortcut-key">{shortcut.key.toUpperCase()}</kbd>
                  <span className="shortcut-description">{shortcut.description}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="shortcuts-section">
            <h3>Actions</h3>
            <div className="shortcuts-list">
              {KEYBOARD_SHORTCUTS.filter(s => 
                ['toggleRead', 'toggleStar', 'refresh', 'newHaunt'].includes(s.action)
              ).map(shortcut => (
                <div key={shortcut.key} className="shortcut-item">
                  <kbd className="shortcut-key">{shortcut.key.toUpperCase()}</kbd>
                  <span className="shortcut-description">{shortcut.description}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="shortcuts-section">
            <h3>Help</h3>
            <div className="shortcuts-list">
              {KEYBOARD_SHORTCUTS.filter(s => 
                s.action === 'showHelp'
              ).map(shortcut => (
                <div key={shortcut.key} className="shortcut-item">
                  <kbd className="shortcut-key">{shortcut.key}</kbd>
                  <span className="shortcut-description">{shortcut.description}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="shortcuts-footer">
          <p className="shortcuts-note">
            Press <kbd>ESC</kbd> to close this dialog
          </p>
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcutsHelp;
