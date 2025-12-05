import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AuthState, LoginRequest, User } from '../../types';
import apiClient from '../../services/api';

const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!localStorage.getItem('accessToken'),
  loading: false,
  error: null,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.login(credentials);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (userData: any, { rejectWithValue }) => {
    try {
      const response = await apiClient.register(userData);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async () => {
    await apiClient.logout();
  }
);

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      console.log('[fetchCurrentUser] Starting user fetch...');
      const user = await apiClient.getCurrentUser();
      console.log('[fetchCurrentUser] User fetched successfully:', user.email);
      return user;
    } catch (error: any) {
      console.error('[fetchCurrentUser] Failed to fetch user:', error.message);
      return rejectWithValue(error.message);
    }
  }
);

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.refreshToken();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder.addCase(login.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(login.fulfilled, (state, action) => {
      state.loading = false;
      state.user = action.payload.user;
      state.accessToken = action.payload.access;
      state.refreshToken = action.payload.refresh;
      state.isAuthenticated = true;
      state.error = null;
      // Store tokens in localStorage
      localStorage.setItem('accessToken', action.payload.access);
      localStorage.setItem('refreshToken', action.payload.refresh);
      // Update apiClient token
      apiClient.setAccessToken(action.payload.access);
      
      console.log('[authSlice] Login successful!');
      console.log('[authSlice] Token saved to localStorage:', !!localStorage.getItem('accessToken'));
      console.log('[authSlice] User:', action.payload.user.email);
    });
    builder.addCase(login.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
      state.isAuthenticated = false;
    });

    // Register
    builder.addCase(register.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(register.fulfilled, (state, action) => {
      state.loading = false;
      state.user = action.payload.user;
      state.accessToken = action.payload.access;
      state.refreshToken = action.payload.refresh;
      state.isAuthenticated = true;
      state.error = null;
      // Store tokens in localStorage
      localStorage.setItem('accessToken', action.payload.access);
      localStorage.setItem('refreshToken', action.payload.refresh);
      // Update apiClient token
      apiClient.setAccessToken(action.payload.access);
      
      console.log('[authSlice] Registration successful!');
      console.log('[authSlice] Token saved to localStorage:', !!localStorage.getItem('accessToken'));
      console.log('[authSlice] User:', action.payload.user.email);
    });
    builder.addCase(register.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
      state.isAuthenticated = false;
    });

    // Logout
    builder.addCase(logout.fulfilled, (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.error = null;
      // Clear tokens from localStorage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    });

    // Fetch current user
    builder.addCase(fetchCurrentUser.pending, (state) => {
      state.loading = true;
    });
    builder.addCase(fetchCurrentUser.fulfilled, (state, action) => {
      state.loading = false;
      state.user = action.payload;
      state.isAuthenticated = true;
    });
    builder.addCase(fetchCurrentUser.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
      console.error('[authSlice] fetchCurrentUser rejected:', action.payload);
      
      // IMPORTANT: Don't clear authentication state here!
      // The API client will handle 401 errors and redirect to login if needed.
      // Clearing tokens here causes the user to be logged out even on network errors.
      // The token remains valid until the API client explicitly clears it on a real 401.
    });

    // Refresh token
    builder.addCase(refreshToken.fulfilled, (state, action) => {
      state.accessToken = action.payload.access;
    });
    builder.addCase(refreshToken.rejected, (state) => {
      console.error('[authSlice] refreshToken rejected');
      // Don't clear tokens here - let the API client handle it
      // The API client will clear tokens and redirect on actual auth failures
    });
  },
});

export const { clearError, setUser } = authSlice.actions;
export default authSlice.reducer;
