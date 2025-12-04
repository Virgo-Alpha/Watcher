/**
 * Format a date string to a relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) {
    return 'just now';
  } else if (diffMin < 60) {
    return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
  } else if (diffHour < 24) {
    return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
  } else if (diffDay < 7) {
    return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString();
  }
};

/**
 * Format a date string to a readable format
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

/**
 * Truncate text to a maximum length
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '...';
};

/**
 * Parse status change from description text
 * Supports formats like "Key: OLD → NEW" or "Key changed from OLD to NEW"
 */
export interface StatusChange {
  key: string;
  oldValue: string;
  newValue: string;
}

export const parseStatusChange = (description: string): StatusChange | null => {
  // Try to extract status change in format "Key: OLD → NEW"
  const arrowMatch = description.match(/^(.+?):\s*(.+?)\s*→\s*(.+?)$/);
  if (arrowMatch) {
    return {
      key: arrowMatch[1].trim(),
      oldValue: arrowMatch[2].trim(),
      newValue: arrowMatch[3].trim(),
    };
  }
  
  // Try format "Key changed from OLD to NEW"
  const changedMatch = description.match(/^(.+?)\s+changed from\s+(.+?)\s+to\s+(.+?)$/i);
  if (changedMatch) {
    return {
      key: changedMatch[1].trim(),
      oldValue: changedMatch[2].trim(),
      newValue: changedMatch[3].trim(),
    };
  }
  
  return null;
};

/**
 * Parse multiple status changes from description text
 * Each line can contain a status change
 */
export const parseStatusChanges = (description: string): StatusChange[] => {
  const changes: StatusChange[] = [];
  
  // Split by newlines and try to parse each line
  const lines = description.split('\n');
  for (const line of lines) {
    const change = parseStatusChange(line);
    if (change) {
      changes.push(change);
    }
  }
  
  return changes;
};
