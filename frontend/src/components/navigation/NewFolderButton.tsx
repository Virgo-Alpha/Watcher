import React, { useState } from 'react';
import './NewFolderButton.css';

interface NewFolderButtonProps {
  onCreateFolder: (name: string) => void;
}

const NewFolderButton: React.FC<NewFolderButtonProps> = ({ onCreateFolder }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [folderName, setFolderName] = useState('');

  const handleStartCreate = () => {
    setIsCreating(true);
  };

  const handleCancel = () => {
    setIsCreating(false);
    setFolderName('');
  };

  const handleCreate = () => {
    if (folderName.trim()) {
      onCreateFolder(folderName.trim());
      setIsCreating(false);
      setFolderName('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCreate();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (isCreating) {
    return (
      <div className="new-folder-input-container">
        <input
          type="text"
          className="new-folder-input"
          placeholder="Folder name..."
          value={folderName}
          onChange={(e) => setFolderName(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <div className="new-folder-actions">
          <button className="new-folder-btn create" onClick={handleCreate}>
            ✓
          </button>
          <button className="new-folder-btn cancel" onClick={handleCancel}>
            ✕
          </button>
        </div>
      </div>
    );
  }

  return (
    <button className="new-folder-button" onClick={handleStartCreate}>
      <span className="new-folder-icon">📁+</span>
      <span>New Folder</span>
    </button>
  );
};

export default NewFolderButton;
