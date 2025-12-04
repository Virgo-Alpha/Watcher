import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { UIState, UserUIPreferences } from '../../types';
import apiClient from '../../services/api';

const initialState: UIState = {
  leftPanelWidth: 250,
  middlePanelWidth: 400,
  showSetupWizard: false,
  keyboardShortcutsEnabled: true,
  autoMarkReadOnScroll: false,
  collapsedFolders: [],
};

// Async thunks
export const fetchUserPreferences = createAsyncThunk(
  'ui/fetchUserPreferences',
  async (_, { rejectWithValue }) => {
    try {
      const preferences = await apiClient.getUserPreferences();
      return preferences;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateUserPreferences = createAsyncThunk(
  'ui/updateUserPreferences',
  async (data: Partial<UserUIPreferences>, { rejectWithValue }) => {
    try {
      const preferences = await apiClient.updateUserPreferences(data);
      return preferences;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setLeftPanelWidth: (state, action: PayloadAction<number>) => {
      state.leftPanelWidth = action.payload;
    },
    setMiddlePanelWidth: (state, action: PayloadAction<number>) => {
      state.middlePanelWidth = action.payload;
    },
    setShowSetupWizard: (state, action: PayloadAction<boolean>) => {
      state.showSetupWizard = action.payload;
    },
    setKeyboardShortcutsEnabled: (state, action: PayloadAction<boolean>) => {
      state.keyboardShortcutsEnabled = action.payload;
    },
    setAutoMarkReadOnScroll: (state, action: PayloadAction<boolean>) => {
      state.autoMarkReadOnScroll = action.payload;
    },
    toggleFolder: (state, action: PayloadAction<string>) => {
      const folderId = action.payload;
      const index = state.collapsedFolders.indexOf(folderId);
      if (index !== -1) {
        state.collapsedFolders.splice(index, 1);
      } else {
        state.collapsedFolders.push(folderId);
      }
    },
    collapseFolder: (state, action: PayloadAction<string>) => {
      if (!state.collapsedFolders.includes(action.payload)) {
        state.collapsedFolders.push(action.payload);
      }
    },
    expandFolder: (state, action: PayloadAction<string>) => {
      state.collapsedFolders = state.collapsedFolders.filter(id => id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    // Fetch user preferences
    builder.addCase(fetchUserPreferences.fulfilled, (state, action) => {
      state.leftPanelWidth = action.payload.left_panel_width;
      state.middlePanelWidth = action.payload.middle_panel_width;
      state.keyboardShortcutsEnabled = action.payload.keyboard_shortcuts_enabled;
      state.autoMarkReadOnScroll = action.payload.auto_mark_read_on_scroll;
      state.collapsedFolders = action.payload.collapsed_folders;
    });

    // Update user preferences
    builder.addCase(updateUserPreferences.fulfilled, (state, action) => {
      state.leftPanelWidth = action.payload.left_panel_width;
      state.middlePanelWidth = action.payload.middle_panel_width;
      state.keyboardShortcutsEnabled = action.payload.keyboard_shortcuts_enabled;
      state.autoMarkReadOnScroll = action.payload.auto_mark_read_on_scroll;
      state.collapsedFolders = action.payload.collapsed_folders;
    });
  },
});

export const {
  setLeftPanelWidth,
  setMiddlePanelWidth,
  setShowSetupWizard,
  setKeyboardShortcutsEnabled,
  setAutoMarkReadOnScroll,
  toggleFolder,
  collapseFolder,
  expandFolder,
} = uiSlice.actions;

export default uiSlice.reducer;
