import rssItemsReducer, {
  setSelectedItem,
  clearError,
  updateUnreadCount,
  fetchRSSItems,
  fetchRSSItem,
  fetchReadStates,
  markAsRead,
  markAsUnread,
  toggleStar,
  bulkMarkAsRead,
} from './rssItemsSlice';
import { RSSItemsState, RSSItem, UserReadState } from '../../types';

describe('rssItemsSlice', () =>