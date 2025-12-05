import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { RSSItemsState, RSSItem, UserReadState } from '../../types';
import apiClient from '../../services/api';

const initialState: RSSItemsState = {
  items: [],
  selectedItem: null,
  unreadCounts: {},
  readStates: {},
  loading: false,
  error: null,
};

// Async thunks
export const fetchRSSItems = createAsyncThunk(
  'rssItems/fetchRSSItems',
  async (hauntId: string | undefined, { rejectWithValue }) => {
    try {
      const items = await apiClient.getRSSItems(hauntId);
      return items;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchRSSItem = createAsyncThunk(
  'rssItems/fetchRSSItem',
  async (id: string, { rejectWithValue }) => {
    try {
      const item = await apiClient.getRSSItem(id);
      return item;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchReadStates = createAsyncThunk(
  'rssItems/fetchReadStates',
  async (hauntId: string | undefined, { rejectWithValue }) => {
    try {
      const states = await apiClient.getReadStates(hauntId);
      return states;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const markAsRead = createAsyncThunk(
  'rssItems/markAsRead',
  async (itemId: string, { rejectWithValue }) => {
    try {
      const state = await apiClient.markAsRead(itemId);
      return state;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const markAsUnread = createAsyncThunk(
  'rssItems/markAsUnread',
  async (itemId: string, { rejectWithValue }) => {
    try {
      const state = await apiClient.markAsUnread(itemId);
      return state;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const toggleStar = createAsyncThunk(
  'rssItems/toggleStar',
  async (itemId: string, { rejectWithValue }) => {
    try {
      const state = await apiClient.toggleStar(itemId);
      return state;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const bulkMarkAsRead = createAsyncThunk(
  'rssItems/bulkMarkAsRead',
  async (itemIds: string[], { rejectWithValue }) => {
    try {
      await apiClient.bulkMarkAsRead(itemIds);
      return itemIds;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

const rssItemsSlice = createSlice({
  name: 'rssItems',
  initialState,
  reducers: {
    setSelectedItem: (state, action: PayloadAction<RSSItem | null>) => {
      state.selectedItem = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateUnreadCount: (state, action: PayloadAction<{ hauntId: string; count: number }>) => {
      state.unreadCounts[action.payload.hauntId] = action.payload.count;
    },
  },
  extraReducers: (builder) => {
    // Fetch RSS items
    builder.addCase(fetchRSSItems.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchRSSItems.fulfilled, (state, action) => {
      state.loading = false;
      state.items = action.payload;
    });
    builder.addCase(fetchRSSItems.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch single RSS item
    builder.addCase(fetchRSSItem.fulfilled, (state, action) => {
      const index = state.items.findIndex(i => i.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      } else {
        state.items.push(action.payload);
      }
    });

    // Fetch read states
    builder.addCase(fetchReadStates.fulfilled, (state, action) => {
      const statesMap: Record<string, UserReadState> = {};
      const payload = Array.isArray(action.payload) ? action.payload : [];
      payload.forEach(state => {
        statesMap[state.rss_item] = state;
      });
      state.readStates = statesMap;
    });

    // Mark as read
    builder.addCase(markAsRead.fulfilled, (state, action) => {
      state.readStates[action.payload.rss_item] = action.payload;
    });

    // Mark as unread
    builder.addCase(markAsUnread.fulfilled, (state, action) => {
      state.readStates[action.payload.rss_item] = action.payload;
    });

    // Toggle star
    builder.addCase(toggleStar.fulfilled, (state, action) => {
      state.readStates[action.payload.rss_item] = action.payload;
    });

    // Bulk mark as read
    builder.addCase(bulkMarkAsRead.fulfilled, (state, action) => {
      action.payload.forEach(itemId => {
        if (state.readStates[itemId]) {
          state.readStates[itemId].is_read = true;
        }
      });
    });
  },
});

export const { setSelectedItem, clearError, updateUnreadCount } = rssItemsSlice.actions;
export default rssItemsSlice.reducer;
