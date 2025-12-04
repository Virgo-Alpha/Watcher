import { RSSItem } from '../types';

export type ShortcutAction =
  | 'nextItem'
  | 'previousItem'
  | 'toggleRead'
  | 'toggleStar'
  | 'refresh'
  | 'newHaunt'
  | 'showHelp';

export interface KeyboardShortcut {
  key: string;
  action: ShortcutAction;
  description: string;
  requiresSelection?: boolean;
}

export const KEYBOARD_SHORTCUTS: KeyboardShortcut[] = [
  { key: 'j', action: 'nextItem', description: 'Next item' },
  { key: 'k', action: 'previousItem', description: 'Previous item' },
  { key: 'm', action: 'toggleRead', description: 'Toggle read/unread', requiresSelection: true },
  { key: 's', action: 'toggleStar', description: 'Toggle star', requiresSelection: true },
  { key: 'r', action: 'refresh', description: 'Refresh current haunt' },
  { key: 'n', action: 'newHaunt', description: 'Create new haunt' },
  { key: '?', action: 'showHelp', description: 'Show keyboard shortcuts' },
];

export interface KeyboardShortcutHandlers {
  onNextItem: () => void;
  onPreviousItem: () => void;
  onToggleRead: () => void;
  onToggleStar: () => void;
  onRefresh: () => void;
  onNewHaunt: () => void;
  onShowHelp: () => void;
}

export class KeyboardShortcutManager {
  private handlers: KeyboardShortcutHandlers;
  private enabled: boolean = true;

  constructor(handlers: KeyboardShortcutHandlers) {
    this.handlers = handlers;
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  handleKeyPress = (event: KeyboardEvent) => {
    // Don't handle shortcuts if user is typing in an input field
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return;
    }

    // Don't handle if shortcuts are disabled
    if (!this.enabled) {
      return;
    }

    const key = event.key.toLowerCase();

    switch (key) {
      case 'j':
        event.preventDefault();
        this.handlers.onNextItem();
        break;
      case 'k':
        event.preventDefault();
        this.handlers.onPreviousItem();
        break;
      case 'm':
        event.preventDefault();
        this.handlers.onToggleRead();
        break;
      case 's':
        event.preventDefault();
        this.handlers.onToggleStar();
        break;
      case 'r':
        event.preventDefault();
        this.handlers.onRefresh();
        break;
      case 'n':
        event.preventDefault();
        this.handlers.onNewHaunt();
        break;
      case '?':
        event.preventDefault();
        this.handlers.onShowHelp();
        break;
    }
  };

  attach() {
    document.addEventListener('keydown', this.handleKeyPress);
  }

  detach() {
    document.removeEventListener('keydown', this.handleKeyPress);
  }
}

export const getNextItem = (items: RSSItem[], currentItem: RSSItem | null): RSSItem | null => {
  if (items.length === 0) return null;
  if (!currentItem) return items[0];

  const currentIndex = items.findIndex(item => item.id === currentItem.id);
  if (currentIndex === -1 || currentIndex === items.length - 1) return currentItem;

  return items[currentIndex + 1];
};

export const getPreviousItem = (items: RSSItem[], currentItem: RSSItem | null): RSSItem | null => {
  if (items.length === 0) return null;
  if (!currentItem) return items[0];

  const currentIndex = items.findIndex(item => item.id === currentItem.id);
  if (currentIndex === -1 || currentIndex === 0) return currentItem;

  return items[currentIndex - 1];
};
