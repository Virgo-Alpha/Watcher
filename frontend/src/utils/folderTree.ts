import { Folder, Haunt, FolderTree } from '../types';

/**
 * Build a hierarchical folder tree from flat folder and haunt arrays
 */
export const buildFolderTree = (
  folders: Folder[],
  haunts: Haunt[],
  collapsedFolders: string[] = []
): FolderTree[] => {
  // Create a map of folders by ID
  const folderMap = new Map<string, FolderTree>();
  
  // Initialize all folders
  folders.forEach(folder => {
    folderMap.set(folder.id, {
      ...folder,
      children: [],
      haunts: [],
      unread_count: 0,
      is_expanded: !collapsedFolders.includes(folder.id),
    });
  });

  // Assign haunts to their folders
  haunts.forEach(haunt => {
    if (haunt.folder) {
      const folder = folderMap.get(haunt.folder);
      if (folder) {
        folder.haunts.push(haunt);
        folder.unread_count += haunt.unread_count || 0;
      }
    }
  });

  // Build the tree structure
  const rootFolders: FolderTree[] = [];
  
  folderMap.forEach(folder => {
    if (folder.parent) {
      const parentFolder = folderMap.get(folder.parent);
      if (parentFolder) {
        parentFolder.children.push(folder);
        // Propagate unread counts up the tree
        parentFolder.unread_count += folder.unread_count;
      }
    } else {
      rootFolders.push(folder);
    }
  });

  return rootFolders;
};

/**
 * Get all haunts that don't belong to any folder
 */
export const getUnfolderedHaunts = (haunts: Haunt[]): Haunt[] => {
  return haunts.filter(haunt => !haunt.folder);
};

/**
 * Flatten a folder tree to get all folder IDs in order
 */
export const flattenFolderTree = (tree: FolderTree[]): string[] => {
  const result: string[] = [];
  
  const traverse = (folders: FolderTree[]) => {
    folders.forEach(folder => {
      result.push(folder.id);
      if (folder.children.length > 0) {
        traverse(folder.children);
      }
    });
  };
  
  traverse(tree);
  return result;
};
