import React, { useState } from 'react';
import { FolderTree as FolderTreeType, Haunt } from '../../types';
import FolderItem from './FolderItem';
import HauntItem from './HauntItem';
import ContextMenu from './ContextMenu';
import './FolderTree.css';

interface FolderTreeProps {
  folders: FolderTreeType[];
  unfolderedHaunts: Haunt[];
  selectedHauntId: string | null;
  onHauntSelect: (haunt: Haunt) => void;
  onFolderToggle: (folderId: string) => void;
  onFolderCreate: (name: string, parentId: string | null) => void;
  onFolderRename: (folderId: string, newName: string) => void;
  onFolderDelete: (folderId: string) => void;
  onHauntMove: (hauntId: string, folderId: string | null) => void;
  onHauntDelete: (hauntId: string) => void;
}

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  type: 'folder' | 'haunt' | null;
  targetId: string | null;
  targetName: string | null;
}

const FolderTree: React.FC<FolderTreeProps> = ({
  folders,
  unfolderedHaunts,
  selectedHauntId,
  onHauntSelect,
  onFolderToggle,
  onFolderCreate,
  onFolderRename,
  onFolderDelete,
  onHauntMove,
  onHauntDelete,
}) => {
  const [draggedHaunt, setDraggedHaunt] = useState<Haunt | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    type: null,
    targetId: null,
    targetName: null,
  });

  const handleDragStart = (haunt: Haunt) => {
    setDraggedHaunt(haunt);
  };

  const handleDragEnd = () => {
    setDraggedHaunt(null);
    setDropTarget(null);
  };

  const handleDragOver = (e: React.DragEvent, folderId: string | null) => {
    e.preventDefault();
    setDropTarget(folderId);
  };

  const handleDragLeave = () => {
    setDropTarget(null);
  };

  const handleDrop = (e: React.DragEvent, folderId: string | null) => {
    e.preventDefault();
    if (draggedHaunt && draggedHaunt.folder !== folderId) {
      onHauntMove(draggedHaunt.id, folderId);
    }
    setDraggedHaunt(null);
    setDropTarget(null);
  };

  const handleContextMenu = (
    e: React.MouseEvent,
    type: 'folder' | 'haunt',
    id: string,
    name: string
  ) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      type,
      targetId: id,
      targetName: name,
    });
  };

  const handleCloseContextMenu = () => {
    setContextMenu({
      visible: false,
      x: 0,
      y: 0,
      type: null,
      targetId: null,
      targetName: null,
    });
  };

  const handleContextMenuAction = (action: string) => {
    if (!contextMenu.targetId) return;

    switch (action) {
      case 'rename':
        if (contextMenu.type === 'folder') {
          const newName = prompt('Enter new folder name:', contextMenu.targetName || '');
          if (newName && newName.trim()) {
            onFolderRename(contextMenu.targetId, newName.trim());
          }
        }
        break;
      case 'delete':
        if (contextMenu.type === 'folder') {
          if (window.confirm(`Delete folder "${contextMenu.targetName}"?`)) {
            onFolderDelete(contextMenu.targetId);
          }
        } else if (contextMenu.type === 'haunt') {
          if (window.confirm(`Delete haunt "${contextMenu.targetName}"?`)) {
            onHauntDelete(contextMenu.targetId);
          }
        }
        break;
      case 'createSubfolder':
        const subfolderName = prompt('Enter subfolder name:');
        if (subfolderName && subfolderName.trim()) {
          onFolderCreate(subfolderName.trim(), contextMenu.targetId);
        }
        break;
    }

    handleCloseContextMenu();
  };

  const renderFolder = (folder: FolderTreeType, depth: number = 0) => {
    const isDropTarget = dropTarget === folder.id;

    return (
      <div key={folder.id} className="folder-tree-item">
        <FolderItem
          folder={folder}
          depth={depth}
          isDropTarget={isDropTarget}
          onToggle={() => onFolderToggle(folder.id)}
          onDragOver={(e) => handleDragOver(e, folder.id)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, folder.id)}
          onContextMenu={(e) => handleContextMenu(e, 'folder', folder.id, folder.name)}
        />

        {folder.is_expanded && (
          <div className="folder-children">
            {/* Render haunts in this folder */}
            {folder.haunts.map((haunt) => (
              <HauntItem
                key={haunt.id}
                haunt={haunt}
                depth={depth + 1}
                isSelected={selectedHauntId === haunt.id}
                isDragging={draggedHaunt?.id === haunt.id}
                onSelect={() => onHauntSelect(haunt)}
                onDragStart={() => handleDragStart(haunt)}
                onDragEnd={handleDragEnd}
                onContextMenu={(e) => handleContextMenu(e, 'haunt', haunt.id, haunt.name)}
              />
            ))}

            {/* Render subfolders */}
            {folder.children.map((child) => renderFolder(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="folder-tree-container">
      {/* Root folders */}
      {folders.map((folder) => renderFolder(folder, 0))}

      {/* Unfolderd haunts section */}
      {unfolderedHaunts.length > 0 && (
        <div
          className={`unfolderd-section ${dropTarget === null ? 'drop-target' : ''}`}
          onDragOver={(e) => handleDragOver(e, null)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, null)}
        >
          <div className="folder-header-simple">
            <span className="folder-name">Uncategorized</span>
          </div>
          <div className="folder-children">
            {unfolderedHaunts.map((haunt) => (
              <HauntItem
                key={haunt.id}
                haunt={haunt}
                depth={0}
                isSelected={selectedHauntId === haunt.id}
                isDragging={draggedHaunt?.id === haunt.id}
                onSelect={() => onHauntSelect(haunt)}
                onDragStart={() => handleDragStart(haunt)}
                onDragEnd={handleDragEnd}
                onContextMenu={(e) => handleContextMenu(e, 'haunt', haunt.id, haunt.name)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Context Menu */}
      {contextMenu.visible && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          type={contextMenu.type!}
          onAction={handleContextMenuAction}
          onClose={handleCloseContextMenu}
        />
      )}
    </div>
  );
};

export default FolderTree;
