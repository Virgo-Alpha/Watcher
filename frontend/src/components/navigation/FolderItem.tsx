import React from 'react';
import { FolderTree } from '../../types';
import './FolderItem.css';

interface FolderItemProps {
  folder: FolderTree;
  depth: number;
  isDropTarget: boolean;
  onToggle: () => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

const FolderItem: React.FC<FolderItemProps> = ({
  folder,
  depth,
  isDropTarget,
  onToggle,
  onDragOver,
  onDragLeave,
  onDrop,
  onContextMenu,
}) => {
  const hasChildren = folder.children.length > 0 || folder.haunts.length > 0;

  return (
    <div
      className={`folder-item ${isDropTarget ? 'drop-target' : ''}`}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onContextMenu={onContextMenu}
    >
      <div className="folder-item-content" onClick={onToggle}>
        {hasChildren && (
          <span className={`folder-icon ${folder.is_expanded ? 'expanded' : 'collapsed'}`}>
            {folder.is_expanded ? '▼' : '▶'}
          </span>
        )}
        {!hasChildren && <span className="folder-icon-spacer" />}
        
        <span className="folder-icon-folder">📁</span>
        <span className="folder-name">{folder.name}</span>
        
        {folder.unread_count > 0 && (
          <span className="unread-badge">{folder.unread_count}</span>
        )}
      </div>
    </div>
  );
};

export default FolderItem;
