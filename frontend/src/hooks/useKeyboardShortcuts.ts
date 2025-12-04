import { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from './index';
import { setSelectedItem, markAsRead, markAsUnread, toggleStar } from '../store/slices/rssItemsSlice';
import { refreshHaunt } from '../store/slices/hauntsSlice';
import { setShowSetupWizard } from '../store/slices/uiSlice';
import { KeyboardShortcutManager, getNextItem, getPreviousItem } from '../services/keyboardShortcuts';

export const useKeyboardShortcuts = () => {
  const dispatch = useAppDispatch();
  const { items, selectedItem, readStates } = useAppSelector((state) => state.rssItems);
  const { selectedHaunt } = useAppSelector((state) => state.haunts);
  const { keyboardShortcutsEnabled } = useAppSelector((state) => state.ui);
  
  const [showHelp, setShowHelp] = useState(false);
  const managerRef = useRef<KeyboardShortcutManager | null>(null);

  useEffect(() => {
    const handlers = {
      onNextItem: () => {
        const nextItem = getNextItem(items, selectedItem);
        if (nextItem && nextItem.id !== selectedItem?.id) {
          dispatch(setSelectedItem(nextItem));
          
          // Auto-mark as read
          const readState = readStates[nextItem.id];
          if (!readState?.is_read) {
            dispatch(markAsRead(nextItem.id));
          }
          
          // Scroll item into view
          scrollItemIntoView(nextItem.id);
        }
      },
      onPreviousItem: () => {
        const prevItem = getPreviousItem(items, selectedItem);
        if (prevItem && prevItem.id !== selectedItem?.id) {
          dispatch(setSelectedItem(prevItem));
          
          // Auto-mark as read
          const readState = readStates[prevItem.id];
          if (!readState?.is_read) {
            dispatch(markAsRead(prevItem.id));
          }
          
          // Scroll item into view
          scrollItemIntoView(prevItem.id);
        }
      },
      onToggleRead: () => {
        if (!selectedItem) return;
        
        const readState = readStates[selectedItem.id];
        if (readState?.is_read) {
          dispatch(markAsUnread(selectedItem.id));
        } else {
          dispatch(markAsRead(selectedItem.id));
        }
      },
      onToggleStar: () => {
        if (!selectedItem) return;
        dispatch(toggleStar(selectedItem.id));
      },
      onRefresh: () => {
        if (!selectedHaunt) return;
        dispatch(refreshHaunt(selectedHaunt.id));
      },
      onNewHaunt: () => {
        dispatch(setShowSetupWizard(true));
      },
      onShowHelp: () => {
        setShowHelp(true);
      },
    };

    const manager = new KeyboardShortcutManager(handlers);
    manager.setEnabled(keyboardShortcutsEnabled);
    manager.attach();
    managerRef.current = manager;

    return () => {
      manager.detach();
    };
  }, [
    dispatch,
    items,
    selectedItem,
    selectedHaunt,
    readStates,
    keyboardShortcutsEnabled,
  ]);

  // Update manager enabled state when preference changes
  useEffect(() => {
    if (managerRef.current) {
      managerRef.current.setEnabled(keyboardShortcutsEnabled);
    }
  }, [keyboardShortcutsEnabled]);

  return {
    showHelp,
    setShowHelp,
  };
};

const scrollItemIntoView = (itemId: string) => {
  // Find the item card element and scroll it into view
  const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
  if (itemElement) {
    itemElement.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
    });
  }
};
