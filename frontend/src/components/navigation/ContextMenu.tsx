import React, { useEffect, useRef } from 'react';
import './ContextMenu.css';

interface ContextMenuProps {
  x: number;
  y: number;
  type: 'folder' | 'haunt';
  onAction: (action: string) => void;
  onClose: () => void;
}

const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, type, onAction, onClose }) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const folderActions = [
    { id: 'rename', label: 'Rename Folder', icon: '✏️' },
    { id: 'createSubfolder', label: 'Create Subfolder', icon: '➕' },
    { id: 'delete', label: 'Delete Folder', icon: '🗑️', danger: true },
  ];

  const hauntActions = [
    { id: 'edit', label: 'Edit Haunt', icon: '✏️' },
    { id: 'refresh', label: 'Refresh Now', icon: '🔄' },
    { id: 'delete', label: 'Delete Haunt', icon: '🗑️', danger: true },
  ];

  const actions = type === 'folder' ? folderActions : hauntActions;

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{ left: `${x}px`, top: `${y}px` }}
    >
      {actions.map((action) => (
        <div
          key={action.id}
          className={`context-menu-item ${action.danger ? 'danger' : ''}`}
          onClick={() => onAction(action.id)}
        >
          <span className="context-menu-icon">{action.icon}</span>
          <span className="context-menu-label">{action.label}</span>
        </div>
      ))}
    </div>
  );
};

export default ContextMenu;
