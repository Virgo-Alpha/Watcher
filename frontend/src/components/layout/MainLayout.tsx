import React, { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { setLeftPanelWidth, setMiddlePanelWidth, updateUserPreferences } from '../../store/slices/uiSlice';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import NavigationPanel from './NavigationPanel';
import ItemListPanel from './ItemListPanel';
import ItemDetailPanel from './ItemDetailPanel';
import SetupWizard from '../wizard/SetupWizard';
import KeyboardShortcutsHelp from '../common/KeyboardShortcutsHelp';
import './MainLayout.css';

const MainLayout: React.FC = () => {
  const dispatch = useAppDispatch();
  const { leftPanelWidth, middlePanelWidth } = useAppSelector((state) => state.ui);
  const { showHelp, setShowHelp } = useKeyboardShortcuts();

  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingMiddle, setIsResizingMiddle] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle left panel resize
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingLeft || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidth = e.clientX - containerRect.left;
      
      if (newWidth >= 200 && newWidth <= 400) {
        dispatch(setLeftPanelWidth(newWidth));
      }
    };

    const handleMouseUp = () => {
      if (isResizingLeft) {
        setIsResizingLeft(false);
        // Save to backend
        dispatch(updateUserPreferences({ left_panel_width: leftPanelWidth }));
      }
    };

    if (isResizingLeft) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingLeft, leftPanelWidth, dispatch]);

  // Handle middle panel resize
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingMiddle || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidth = e.clientX - containerRect.left - leftPanelWidth;
      
      if (newWidth >= 300 && newWidth <= 600) {
        dispatch(setMiddlePanelWidth(newWidth));
      }
    };

    const handleMouseUp = () => {
      if (isResizingMiddle) {
        setIsResizingMiddle(false);
        // Save to backend
        dispatch(updateUserPreferences({ middle_panel_width: middlePanelWidth }));
      }
    };

    if (isResizingMiddle) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingMiddle, middlePanelWidth, leftPanelWidth, dispatch]);

  return (
    <>
      <div className="main-layout" ref={containerRef}>
        <div 
          className="panel navigation-panel" 
          style={{ width: `${leftPanelWidth}px` }}
        >
          <NavigationPanel />
        </div>
        
        <div 
          className="resize-handle"
          onMouseDown={() => setIsResizingLeft(true)}
        />
        
        <div 
          className="panel item-list-panel" 
          style={{ width: `${middlePanelWidth}px` }}
        >
          <ItemListPanel />
        </div>
        
        <div 
          className="resize-handle"
          onMouseDown={() => setIsResizingMiddle(true)}
        />
        
        <div className="panel item-detail-panel">
          <ItemDetailPanel />
        </div>
      </div>
      
      <SetupWizard />
      <KeyboardShortcutsHelp isOpen={showHelp} onClose={() => setShowHelp(false)} />
    </>
  );
};

export default MainLayout;
