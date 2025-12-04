import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import hauntsReducer from './slices/hauntsSlice';
import rssItemsReducer from './slices/rssItemsSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    haunts: hauntsReducer,
    rssItems: rssItemsReducer,
    ui: uiReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;