# Navigation Components

This directory contains the folder organization interface components for the Watcher application.

## Components

### FolderTree
Main component that renders the hierarchical folder structure with haunts.

**Features:**
- Hierarchical folder display with nesting
- Drag-and-drop support for moving haunts between folders
- Context menu integration
- Expand/collapse functionality
- Unread count aggregation

**Props:**
- `folders`: Array of folder tree nodes
- `unfolderedHaunts`: Haunts not assigned to any folder
- `selectedHauntId`: Currently selected haunt ID
- `onHauntSelect`: Callback when a haunt is selected
- `onFolderToggle`: Callback to expand/collapse folders
- `onFolderCreate`: Callback to create new folders
- `onFolderRename`: Callback to rename folders
- `onFolderDelete`: Callback to delete folders
- `onHauntMove`: Callback when a haunt is moved to a different folder
- `onHauntDelete`: Callback to delete haunts

### FolderItem
Renders an individual folder with expand/collapse icon and unread badge.

**Features:**
- Expand/collapse icon (▶/▼)
- Folder emoji icon
- Unread count badge
- Drop target highlighting for drag-and-drop
- Context menu support

### HauntItem
Renders an individual haunt within a folder or uncategorized section.

**Features:**
- Draggable for reorganization
- Selection highlighting
- Unread count badge
- Public indicator for public haunts
- Context menu support

### ContextMenu
Right-click context menu for folder and haunt operations.

**Features:**
- Position-aware rendering
- Different actions for folders vs haunts
- Keyboard support (Escape to close)
- Click-outside to close
- Danger styling for destructive actions

**Folder Actions:**
- Rename Folder
- Create Subfolder
- Delete Folder

**Haunt Actions:**
- Delete Haunt

### NewFolderButton
Button and inline form for creating new root-level folders.

**Features:**
- Inline input field
- Keyboard shortcuts (Enter to create, Escape to cancel)
- Visual feedback
- Auto-focus on input

## Usage

```tsx
import { FolderTree, NewFolderButton } from '../navigation';

// In your component
<NewFolderButton onCreateFolder={handleCreateFolder} />
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
```

## Drag and Drop

Haunts can be dragged and dropped onto:
- Folders (to move into that folder)
- Uncategorized section (to remove from folder)

Visual feedback is provided during drag operations:
- Dragged item becomes semi-transparent
- Drop targets are highlighted with blue border
- Drop zones show background color change

## Context Menu

Right-click on folders or haunts to access context menu:
- **Folders**: Rename, Create Subfolder, Delete
- **Haunts**: Delete

The context menu automatically positions itself and closes when:
- Clicking outside the menu
- Pressing Escape key
- Selecting an action

## Keyboard Shortcuts

- **Enter**: Confirm folder creation
- **Escape**: Cancel folder creation or close context menu

## Styling

Each component has its own CSS file:
- `FolderTree.css`: Container and layout styles
- `FolderItem.css`: Folder item styling
- `HauntItem.css`: Haunt item styling
- `ContextMenu.css`: Context menu styling
- `NewFolderButton.css`: New folder button and input styling

All styles follow the Google Reader-inspired design with:
- Clean, minimal aesthetics
- Subtle hover effects
- Clear visual hierarchy
- Consistent spacing and typography
