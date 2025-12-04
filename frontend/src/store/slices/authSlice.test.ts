import authReducer, { clearError, setUser } from './authSlice';
import { AuthState, User } from '../../types';

describe('authSlice', () => {
  const initialState: AuthState = {
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    loading: false,
    error: null,
  };

  it('should return the initial state', () => {
    expect(authReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should handle clearError', () => {
    const stateWithError: AuthState = {
      ...initialState,
      error: 'Some error',
    };
    const actual = authReducer(stateWithError, clearError());
    expect(actual.error).toBeNull();
  });

  it('should handle setUser', () => {
    const user: User = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
    };
    const actual = authReducer(initialState, setUser(user));
    expect(actual.user).toEqual(user);
  });
});
