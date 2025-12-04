import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import {
  fetchHaunts,
  fetchFolders,
  setSelectedHaunt,
  createFolder,
  updateFolder,
  deleteFolder,
  updateHaunt,
  deleteHaunt,
} from '../../store/slices/hauntsSlice';
import { fetchRSSItems, fetchReadStates } from '../../store/slices/rssItemsSlice';
import { setShowSetupWizard, toggleFolder } from '../../store/slices/uiSlice';
import { Haunt } from '../../types';
import { buildFolderTree, getUnfolderedHaunts } from '../../utils/folderTree';
import FolderTree from '../navigation/FolderTree';
import NewFolderButton from '../navigation/NewFolderButton';
import './NavigationPanel.css';

const NavigationPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: haunts, folders, selectedHaunt, loading } = useAppSelector((state) => state.haunts);
  const { unreadCounts } = useAppSelector((state) => state.rssItems);
  const { collapsedFolders } = useAppSelector((state) => state.ui);

  useEffect(() => {
    dispatch(fetchHaunts());
    dispatch(fetchFolders());
    dispatch(fetchReadStates(undefined));
    // Also fetch subscriptions to show subscribed haunts
    fetchSubscribedHaunts();
  }, [dispatch]);

  const fetchSubscribedHaunts = async () => {
    try {
      const apiClient = require('../../services/api').default;
      await apiClient.getSubscriptions();
      // Subscriptions are already included in the haunts list from the backend
      // The backend should return both owned and subscribed haunts
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
    }
  };

  const handleHauntSelect = (haunt: Haunt) => {
    dispatch(setSelectedHaunt(haunt));
    dispatch(fetchRSSItems(haunt.id));
    dispatch(fetchReadStates(haunt.id));
  };

  const handleNewHaunt = () => {
    dispatch(setShowSetupWizard(true));
  };

  const handleFolderToggle = (folderId: string) => {
    dispatch(toggleFolder(folderId));
  };

  const handleFolderCreate = (name: string, parentId: string | null = null) => {
    dispatch(createFolder({ name, parent: parentId }));
  };

  const handleFolderRename = (folderId: string, newName: string) => {
    dispatch(updateFolder({ id: folderId, data: { name: newName } }));
  };

  const handleFolderDelete = (folderId: string) => {
    dispatch(deleteFolder(folderId));
  };

  const handleHauntMove = (hauntId: string, folderId: string | null) => {
    dispatch(updateHaunt({ id: hauntId, data: { folder: folderId } }));
  };

  const handleHauntDelete = (hauntId: string) => {
    dispatch(deleteHaunt(hauntId));
  };

  // Build folder tree with unread counts
  const hauntsWithUnreadCounts = haunts.map(haunt => ({
    ...haunt,
    unread_count: unreadCounts[haunt.id] || 0,
  }));

  const folderTree = buildFolderTree(folders, hauntsWithUnreadCounts, collapsedFolders);
  const unfolderedHaunts = getUnfolderedHaunts(hauntsWithUnreadCounts);

  if (loading) {
    return (
      <div className="navigation-panel-container">
        <div className="navigation-header">
          <h2>Haunts</h2>
        </div>
        <div className="loading-state">Loading...</div>
      </div>
    );
  }

  return (
    <div className="navigation-panel-container">
      <div className="navigation-header">
        <h2>Haunts</h2>
        <button className="new-haunt-button" onClick={handleNewHaunt}>
          + New Haunt
        </button>
      </div>

      <div className="navigation-content">
        <NewFolderButton onCreateFolder={(name) => handleFolderCreate(name, null)} />

        {haunts.length === 0 && folders.length === 0 ? (
          <div className="empty-state">
            <p>No haunts yet</p>
            <p className="empty-state-hint">Click "New Haunt" to get started</p>
          </div>
        ) : (
          <FolderTree
            folders={folderTree}
            unfolderedHaunts={unfolderedHaunts}
            selectedHauntId={selectedHaunt?.id || null}
            onHauntSelect={handleHauntSelect}
            onFolderToggle={handleFolderToggle}
            onFolderCreate={handleFolderCreate}
            onFolderRename={handleFolderRename}
            onFolderDelete={handleFolderDelete}
            onHauntMove={handleHauntMove}
            onHauntDelete={handleHauntDelete}
          />
        )}
      </div>
    </div>
  );
};

export default NavigationPanel;
