import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { HauntsState, Haunt, Folder, CreateHauntRequest } from '../../types';
import apiClient from '../../services/api';

const initialState: HauntsState = {
  items: [],
  folders: [],
  selectedHaunt: null,
  loading: false,
  error: null,
};

// Async thunks for haunts
export const fetchHaunts = createAsyncThunk(
  'haunts/fetchHaunts',
  async (_, { rejectWithValue }) => {
    try {
      const haunts = await apiClient.getHaunts();
      return haunts;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchHaunt = createAsyncThunk(
  'haunts/fetchHaunt',
  async (id: string, { rejectWithValue }) => {
    try {
      const haunt = await apiClient.getHaunt(id);
      return haunt;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const createHaunt = createAsyncThunk(
  'haunts/createHaunt',
  async (data: CreateHauntRequest, { rejectWithValue }) => {
    try {
      const haunt = await apiClient.createHaunt(data);
      return haunt;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateHaunt = createAsyncThunk(
  'haunts/updateHaunt',
  async ({ id, data }: { id: string; data: Partial<Haunt> }, { rejectWithValue }) => {
    try {
      const haunt = await apiClient.updateHaunt(id, data);
      return haunt;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteHaunt = createAsyncThunk(
  'haunts/deleteHaunt',
  async (id: string, { rejectWithValue }) => {
    try {
      await apiClient.deleteHaunt(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const makeHauntPublic = createAsyncThunk(
  'haunts/makeHauntPublic',
  async (id: string, { rejectWithValue }) => {
    try {
      const haunt = await apiClient.makeHauntPublic(id);
      return haunt;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const refreshHaunt = createAsyncThunk(
  'haunts/refreshHaunt',
  async (id: string, { rejectWithValue }) => {
    try {
      await apiClient.refreshHaunt(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

// Async thunks for folders
export const fetchFolders = createAsyncThunk(
  'haunts/fetchFolders',
  async (_, { rejectWithValue }) => {
    try {
      const folders = await apiClient.getFolders();
      return folders;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const createFolder = createAsyncThunk(
  'haunts/createFolder',
  async ({ name, parent }: { name: string; parent: string | null }, { rejectWithValue }) => {
    try {
      const folder = await apiClient.createFolder(name, parent);
      return folder;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateFolder = createAsyncThunk(
  'haunts/updateFolder',
  async ({ id, data }: { id: string; data: Partial<Folder> }, { rejectWithValue }) => {
    try {
      const folder = await apiClient.updateFolder(id, data);
      return folder;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteFolder = createAsyncThunk(
  'haunts/deleteFolder',
  async (id: string, { rejectWithValue }) => {
    try {
      await apiClient.deleteFolder(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

const hauntsSlice = createSlice({
  name: 'haunts',
  initialState,
  reducers: {
    setSelectedHaunt: (state, action: PayloadAction<Haunt | null>) => {
      state.selectedHaunt = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch haunts
    builder.addCase(fetchHaunts.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchHaunts.fulfilled, (state, action) => {
      state.loading = false;
      state.items = action.payload;
    });
    builder.addCase(fetchHaunts.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch single haunt
    builder.addCase(fetchHaunt.fulfilled, (state, action) => {
      const index = state.items.findIndex(h => h.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      } else {
        state.items.push(action.payload);
      }
    });

    // Create haunt
    builder.addCase(createHaunt.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(createHaunt.fulfilled, (state, action) => {
      state.loading = false;
      state.items.push(action.payload);
    });
    builder.addCase(createHaunt.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Update haunt
    builder.addCase(updateHaunt.fulfilled, (state, action) => {
      const index = state.items.findIndex(h => h.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
      if (state.selectedHaunt?.id === action.payload.id) {
        state.selectedHaunt = action.payload;
      }
    });

    // Delete haunt
    builder.addCase(deleteHaunt.fulfilled, (state, action) => {
      state.items = state.items.filter(h => h.id !== action.payload);
      if (state.selectedHaunt?.id === action.payload) {
        state.selectedHaunt = null;
      }
    });

    // Make haunt public
    builder.addCase(makeHauntPublic.fulfilled, (state, action) => {
      const index = state.items.findIndex(h => h.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
    });

    // Fetch folders
    builder.addCase(fetchFolders.fulfilled, (state, action) => {
      state.folders = action.payload;
    });

    // Create folder
    builder.addCase(createFolder.fulfilled, (state, action) => {
      state.folders.push(action.payload);
    });

    // Update folder
    builder.addCase(updateFolder.fulfilled, (state, action) => {
      const index = state.folders.findIndex(f => f.id === action.payload.id);
      if (index !== -1) {
        state.folders[index] = action.payload;
      }
    });

    // Delete folder
    builder.addCase(deleteFolder.fulfilled, (state, action) => {
      state.folders = state.folders.filter(f => f.id !== action.payload);
    });
  },
});

export const { setSelectedHaunt, clearError } = hauntsSlice.actions;
export default hauntsSlice.reducer;
