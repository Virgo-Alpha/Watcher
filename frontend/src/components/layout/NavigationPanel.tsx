import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  refreshHaunt,
} from '../../store/slices/hauntsSlice';
import { fetchRSSItems, fetchReadStates } from '../../store/slices/rssItemsSlice';
import { setShowSetupWizard, toggleFolder, collapseFolder } from '../../store/slices/uiSlice';
import { logout } from '../../store/slices/authSlice';
import { Haunt } from '../../types';
import { buildFolderTree, getUnfolderedHaunts } from '../../utils/folderTree';
import FolderTree from '../navigation/FolderTree';
import NewFolderButton from '../navigation/NewFolderButton';
import './NavigationPanel.css';

const NavigationPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items: haunts, folders, selectedHaunt, loading } = useAppSelector((state) => state.haunts);
  const { unreadCounts } = useAppSelector((state) => state.rssItems);
  const { collapsedFolders } = useAppSelector((state) => state.ui);
  const { user } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Only fetch data if we have an access token
    const accessToken = localStorage.getItem('accessToken');
    if (accessToken) {
      dispatch(fetchHaunts());
      dispatch(fetchFolders());
      dispatch(fetchReadStates(undefined));
      // Also fetch subscriptions to show subscribed haunts
      fetchSubscribedHaunts();
    }
  }, [dispatch]);

  // Separate effect to collapse folders on first load
  useEffect(() => {
    if (folders.length > 0) {
      // Collapse any folders that aren't already in the collapsed list
      folders.forEach(folder => {
        const folderId = folder.id.toString();
        if (!collapsedFolders.includes(folderId)) {
          dispatch(collapseFolder(folderId));
        }
      });
    }
  }, [folders, collapsedFolders, dispatch]); // Run when folders change or collapsed state changes

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

  const handleHauntEdit = (hauntId: string, data: Partial<Haunt>) => {
    dispatch(updateHaunt({ id: hauntId, data }));
  };

  const handleHauntRefresh = (hauntId: string) => {
    dispatch(refreshHaunt(hauntId));
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
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
        <div className="navigation-header-top">
          <h2>Haunts</h2>
          <button className="logout-button" onClick={handleLogout} title="Logout">
            ⎋
          </button>
        </div>
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
            onHauntEdit={handleHauntEdit}
            onHauntRefresh={handleHauntRefresh}
          />
        )}
      </div>
    </div>
  );
};

export default NavigationPanel;
