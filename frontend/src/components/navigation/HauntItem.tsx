import React from 'react';
import { Haunt } from '../../types';
import './HauntItem.css';

interface HauntItemProps {
  haunt: Haunt;
  depth: number;
  isSelected: boolean;
  isDragging: boolean;
  onSelect: () => void;
  onDragStart: () => void;
  onDragEnd: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

const HauntItem: React.FC<HauntItemProps> = ({
  haunt,
  depth,
  isSelected,
  isDragging,
  onSelect,
  onDragStart,
  onDragEnd,
  onContextMenu,
}) => {
  const unreadCount = haunt.unread_count || 0;

  return (
    <div
      className={`haunt-item ${isSelected ? 'selected' : ''} ${isDragging ? 'dragging' : ''}`}
      style={{ paddingLeft: `${depth * 16 + 32}px` }}
      draggable
      onClick={onSelect}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onContextMenu={onContextMenu}
    >
      <span className="haunt-icon">👻</span>
      <span className="haunt-name">{haunt.name}</span>
      
      {unreadCount > 0 && (
        <span className="unread-badge">{unreadCount}</span>
      )}
      
      {haunt.is_public && (
        <span className="public-indicator" title="Public haunt">🌐</span>
      )}
    </div>
  );
};

export default HauntItem;
