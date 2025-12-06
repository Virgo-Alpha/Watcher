import apiClient from './api';
import {
  User,
  Haunt,
  Folder,
  RSSItem,
  Subscription,
  UserReadState,
  LoginRequest,
  LoginResponse,
  CreateHauntRequest,
  TestScrapeRequest,
  TestScrapeResponse,
  UserUIPreferences,
} from '../types';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
let localStorageStore: Record<string, string> = {};
const localStorageMock = {
  getItem: jest.fn((key: string) => localStorageStore[key] || null),
  setItem: jest.fn((key: string, value: string) => {
    localStorageStore[key] = value;
  }),
  removeItem: jest.fn((key: string) => {
    delete localStorageStore[key];
  }),
  clear: jest.fn(() => {
    localStorageStore = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

describe('API Base URL Configuration', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('should use relative URL when REACT_APP_API_URL is undefined (production default)', () => {
    delete process.env.REACT_APP_API_URL;
    
    // Re-import to get fresh instance with new env
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/api/v1');
    });
  });

  it('should use relative URL when REACT_APP_API_URL is empty string', () => {
    process.env.REACT_APP_API_URL = '';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/api/v1');
    });
  });

  it('should use custom URL when REACT_APP_API_URL is set to a specific value', () => {
    process.env.REACT_APP_API_URL = 'https://api.example.com/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://api.example.com/v1');
    });
  });

  it('should use relative URL when REACT_APP_API_URL is explicitly set to /api/v1', () => {
    process.env.REACT_APP_API_URL = '/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/api/v1');
    });
  });

  it('should handle staging environment URL', () => {
    process.env.REACT_APP_API_URL = 'https://staging-api.example.com/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://staging-api.example.com/api/v1');
    });
  });

  it('should handle production environment with custom domain', () => {
    process.env.REACT_APP_API_URL = 'https://watcher-api.production.com/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://watcher-api.production.com/api/v1');
    });
  });

  it('should correctly construct full URLs with relative base when env var is undefined', () => {
    delete process.env.REACT_APP_API_URL;
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      
      // Mock fetch to capture the URL
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ results: [] }),
      });
      global.fetch = mockFetch;
      
      // Make a request
      client.getHaunts();
      
      // Verify the full URL was constructed correctly
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/haunts/',
        expect.any(Object)
      );
    });
  });

  it('should correctly construct full URLs with relative base', () => {
    process.env.REACT_APP_API_URL = '';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      
      // Mock fetch to capture the URL
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ results: [] }),
      });
      global.fetch = mockFetch;
      
      // Make a request
      client.getHaunts();
      
      // Verify the full URL was constructed correctly
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/haunts/',
        expect.any(Object)
      );
    });
  });

  it('should correctly construct full URLs with custom base', () => {
    process.env.REACT_APP_API_URL = 'https://api.custom.com/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      
      // Mock fetch to capture the URL
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ results: [] }),
      });
      global.fetch = mockFetch;
      
      // Make a request
      client.getHaunts();
      
      // Verify the full URL was constructed correctly
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.custom.com/v1/haunts/',
        expect.any(Object)
      );
    });
  });

  it('should handle undefined vs empty string consistently (both use relative URL)', () => {
    // Test undefined - should use relative URL
    delete process.env.REACT_APP_API_URL;
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/api/v1');
    });

    // Test empty string - should also use relative URL
    process.env.REACT_APP_API_URL = '';
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/api/v1');
    });

    // Both should result in the same relative URL
    expect('/api/v1').toBe('/api/v1');
  });

  it('should use relative URL when REACT_APP_API_URL is set but falsy (empty)', () => {
    process.env.REACT_APP_API_URL = '';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      // Empty string is falsy, so fallback to '/api/v1'
      expect((client as any).baseURL).toBe('/api/v1');
    });
  });

  it('should handle localhost with different ports', () => {
    process.env.REACT_APP_API_URL = 'http://localhost:3001/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('http://localhost:3001/api/v1');
    });
  });

  it('should handle URLs without trailing slash', () => {
    process.env.REACT_APP_API_URL = 'https://api.example.com/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://api.example.com/api/v1');
    });
  });

  it('should handle URLs with trailing slash', () => {
    process.env.REACT_APP_API_URL = 'https://api.example.com/api/v1/';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://api.example.com/api/v1/');
    });
  });

  it('should work with Docker Compose service names', () => {
    process.env.REACT_APP_API_URL = 'http://web:8000/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('http://web:8000/api/v1');
    });
  });

  it('should handle IPv4 addresses', () => {
    process.env.REACT_APP_API_URL = 'http://192.168.1.100:8000/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('http://192.168.1.100:8000/api/v1');
    });
  });

  it('should handle IPv6 addresses', () => {
    process.env.REACT_APP_API_URL = 'http://[::1]:8000/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('http://[::1]:8000/api/v1');
    });
  });

  it('should use localhost URL when explicitly set for development', () => {
    process.env.REACT_APP_API_URL = 'http://localhost:8000/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('http://localhost:8000/api/v1');
    });
  });

  it('should handle null value (treated as falsy)', () => {
    process.env.REACT_APP_API_URL = null as any;
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/api/v1');
    });
  });

  it('should handle whitespace-only string', () => {
    process.env.REACT_APP_API_URL = '   ';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      // Whitespace string is truthy, so it will be used as-is
      expect((client as any).baseURL).toBe('   ');
    });
  });

  it('should handle URL with query parameters', () => {
    process.env.REACT_APP_API_URL = 'https://api.example.com/api/v1?key=value';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://api.example.com/api/v1?key=value');
    });
  });

  it('should handle URL with hash fragment', () => {
    process.env.REACT_APP_API_URL = 'https://api.example.com/api/v1#section';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('https://api.example.com/api/v1#section');
    });
  });

  it('should handle relative path with subdirectory', () => {
    process.env.REACT_APP_API_URL = '/app/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('/app/api/v1');
    });
  });

  it('should handle protocol-relative URL', () => {
    process.env.REACT_APP_API_URL = '//api.example.com/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      expect((client as any).baseURL).toBe('//api.example.com/api/v1');
    });
  });

  it('should correctly construct URLs with different base URL formats', () => {
    const testCases = [
      { env: undefined, expected: '/api/v1/haunts/' },
      { env: '', expected: '/api/v1/haunts/' },
      { env: 'http://localhost:8000/api/v1', expected: 'http://localhost:8000/api/v1/haunts/' },
      { env: 'https://api.prod.com/api/v1', expected: 'https://api.prod.com/api/v1/haunts/' },
      { env: '/custom/api/v1', expected: '/custom/api/v1/haunts/' },
    ];

    testCases.forEach(({ env, expected }) => {
      if (env === undefined) {
        delete process.env.REACT_APP_API_URL;
      } else {
        process.env.REACT_APP_API_URL = env;
      }

      jest.isolateModules(() => {
        const { default: client } = require('./api');
        
        const mockFetch = jest.fn().mockResolvedValue({
          ok: true,
          json: async () => ({ results: [] }),
        });
        global.fetch = mockFetch;
        
        client.getHaunts();
        
        expect(mockFetch).toHaveBeenCalledWith(
          expected,
          expect.any(Object)
        );
      });
    });
  });

  it('should use same-origin relative URL for production builds', () => {
    // Simulate production build where env var is not set
    delete process.env.REACT_APP_API_URL;
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      const baseURL = (client as any).baseURL;
      
      // Should be relative URL (same origin)
      expect(baseURL).toBe('/api/v1');
      expect(baseURL.startsWith('/')).toBe(true);
      expect(baseURL.includes('://')).toBe(false);
    });
  });

  it('should allow cross-origin requests when explicitly configured', () => {
    process.env.REACT_APP_API_URL = 'https://different-domain.com/api/v1';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      const baseURL = (client as any).baseURL;
      
      // Should be absolute URL (cross-origin)
      expect(baseURL).toBe('https://different-domain.com/api/v1');
      expect(baseURL.includes('://')).toBe(true);
    });
  });

  it('should handle zero as env value (falsy but valid)', () => {
    process.env.REACT_APP_API_URL = '0';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      // String '0' is truthy, so it will be used
      expect((client as any).baseURL).toBe('0');
    });
  });

  it('should handle false string as env value', () => {
    process.env.REACT_APP_API_URL = 'false';
    
    jest.isolateModules(() => {
      const { default: client } = require('./api');
      // String 'false' is truthy, so it will be used
      expect((client as any).baseURL).toBe('false');
    });
  });
});

describe('APIClient', () => {
  beforeEach(() => {
    // Clear the store
    localStorageStore = {};
    // Clear mock call history but restore implementations
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
    // Restore implementations
    localStorageMock.getItem.mockImplementation((key: string) => localStorageStore[key] || null);
    localStorageMock.setItem.mockImplementation((key: string, value: string) => {
      localStorageStore[key] = value;
    });
    localStorageMock.removeItem.mockImplementation((key: string) => {
      delete localStorageStore[key];
    });
    localStorageMock.clear.mockImplementation(() => {
      localStorageStore = {};
    });
    (fetch as jest.Mock).mockClear();
  });

  describe('Authentication', () => {
    describe('login', () => {
      it('should login successfully and store tokens', async () => {
        const credentials: LoginRequest = {
          email: 'test@example.com',
          password: 'password123',
        };

        const mockResponse: LoginResponse = {
          access: 'access-token',
          refresh: 'refresh-token',
          user: {
            id: '1',
            email: 'test@example.com',
            username: 'testuser',
          },
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const result = await apiClient.login(credentials);

        expect(result).toEqual(mockResponse);
        expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'access-token');
        expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshToken', 'refresh-token');
      });

      it('should throw error on failed login', async () => {
        const credentials: LoginRequest = {
          email: 'test@example.com',
          password: 'wrong-password',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Invalid credentials' }),
        });

        await expect(apiClient.login(credentials)).rejects.toThrow('Invalid credentials');
      });
    });

    describe('register', () => {
      it('should register successfully and store tokens', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        const mockResponse: LoginResponse = {
          access: 'access-token',
          refresh: 'refresh-token',
          user: {
            id: '1',
            email: 'newuser@example.com',
            username: 'newuser',
          },
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const result = await apiClient.register(userData);

        expect(result).toEqual(mockResponse);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/register/'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify(userData),
          })
        );
        expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'access-token');
        expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshToken', 'refresh-token');
      });

      it('should throw error when passwords do not match', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'different-password',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Passwords do not match' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Passwords do not match');
      });

      it('should throw error when email already exists', async () => {
        const userData = {
          email: 'existing@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Email already registered' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Email already registered');
      });

      it('should throw error when username already exists', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'existinguser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Username already taken' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Username already taken');
      });

      it('should throw error when required fields are missing', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: '',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Username is required' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Username is required');
      });

      it('should throw error when password is too weak', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: '123',
          password_confirm: '123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Password must be at least 8 characters' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Password must be at least 8 characters');
      });

      it('should throw error when email format is invalid', async () => {
        const userData = {
          email: 'invalid-email',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Invalid email format' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Invalid email format');
      });

      it('should handle network errors during registration', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

        await expect(apiClient.register(userData)).rejects.toThrow('Network error');
      });

      it('should handle server errors during registration', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ detail: 'Internal server error' }),
        });

        await expect(apiClient.register(userData)).rejects.toThrow('Internal server error');
      });

      it('should include all user data in request body', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        const mockResponse: LoginResponse = {
          access: 'access-token',
          refresh: 'refresh-token',
          user: {
            id: '1',
            email: 'newuser@example.com',
            username: 'newuser',
          },
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        await apiClient.register(userData);

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/register/'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              email: 'newuser@example.com',
              username: 'newuser',
              password: 'password123',
              password_confirm: 'password123',
              first_name: 'John',
              last_name: 'Doe',
            }),
          })
        );
      });

      it('should set access token before returning response', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        const mockResponse: LoginResponse = {
          access: 'new-access-token',
          refresh: 'new-refresh-token',
          user: {
            id: '1',
            email: 'newuser@example.com',
            username: 'newuser',
          },
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const result = await apiClient.register(userData);

        expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'new-access-token');
        expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshToken', 'new-refresh-token');
        expect(result.access).toBe('new-access-token');
        expect(result.refresh).toBe('new-refresh-token');
      });

      it('should return user data in response', async () => {
        const userData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'password123',
          password_confirm: 'password123',
          first_name: 'John',
          last_name: 'Doe',
        };

        const mockResponse: LoginResponse = {
          access: 'access-token',
          refresh: 'refresh-token',
          user: {
            id: '1',
            email: 'newuser@example.com',
            username: 'newuser',
          },
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const result = await apiClient.register(userData);

        expect(result.user).toEqual({
          id: '1',
          email: 'newuser@example.com',
          username: 'newuser',
        });
      });
    });

    describe('logout', () => {
      it('should clear tokens from storage', async () => {
        localStorageMock.setItem('accessToken', 'token');
        localStorageMock.setItem('refreshToken', 'refresh');

        await apiClient.logout();

        expect(localStorageMock.removeItem).toHaveBeenCalledWith('accessToken');
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('refreshToken');
      });
    });

    describe('refreshToken', () => {
      it('should refresh access token', async () => {
        localStorageMock.setItem('refreshToken', 'refresh-token');

        const mockResponse = { access: 'new-access-token' };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const result = await apiClient.refreshToken();

        expect(result).toEqual(mockResponse);
        expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'new-access-token');
      });

      it('should throw error when no refresh token available', async () => {
        await expect(apiClient.refreshToken()).rejects.toThrow('No refresh token available');
      });
    });

    describe('getCurrentUser', () => {
      it('should fetch current user', async () => {
        const mockUser: User = {
          id: '1',
          email: 'test@example.com',
          username: 'testuser',
        };

        localStorageMock.setItem('accessToken', 'token');

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockUser,
        });

        const result = await apiClient.getCurrentUser();

        expect(result).toEqual(mockUser);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/profile/'),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer token',
            }),
          })
        );
      });
    });
  });

  describe('Haunts', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('getHaunts', () => {
      it('should fetch all haunts with paginated response', async () => {
        const mockHaunts: Haunt[] = [
          {
            id: '1',
            owner: 'user1',
            name: 'Test Haunt',
            url: 'https://example.com',
            description: 'Test description',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'once',
            scrape_interval: 3600,
            is_public: false,
            public_slug: null,
            folder: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ results: mockHaunts }),
        });

        const result = await apiClient.getHaunts();

        expect(result).toEqual(mockHaunts);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/'),
          expect.any(Object)
        );
      });

      it('should fetch all haunts with non-paginated response', async () => {
        const mockHaunts: Haunt[] = [
          {
            id: '1',
            owner: 'user1',
            name: 'Test Haunt',
            url: 'https://example.com',
            description: 'Test description',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'once',
            scrape_interval: 3600,
            is_public: false,
            public_slug: null,
            folder: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHaunts,
        });

        const result = await apiClient.getHaunts();

        expect(result).toEqual(mockHaunts);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/'),
          expect.any(Object)
        );
      });

      it('should handle empty paginated response', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ results: [] }),
        });

        const result = await apiClient.getHaunts();

        expect(result).toEqual([]);
        expect(Array.isArray(result)).toBe(true);
      });

      it('should handle empty non-paginated response', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        });

        const result = await apiClient.getHaunts();

        expect(result).toEqual([]);
        expect(Array.isArray(result)).toBe(true);
      });

      it('should handle paginated response with multiple haunts', async () => {
        const mockHaunts: Haunt[] = [
          {
            id: '1',
            owner: 'user1',
            name: 'Test Haunt 1',
            url: 'https://example1.com',
            description: 'Test description 1',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'once',
            scrape_interval: 3600,
            is_public: false,
            public_slug: null,
            folder: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          {
            id: '2',
            owner: 'user1',
            name: 'Test Haunt 2',
            url: 'https://example2.com',
            description: 'Test description 2',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'on_change',
            scrape_interval: 1800,
            is_public: true,
            public_slug: 'test-haunt-2',
            folder: 'folder1',
            created_at: '2024-01-02T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ results: mockHaunts }),
        });

        const result = await apiClient.getHaunts();

        expect(result).toEqual(mockHaunts);
        expect(result.length).toBe(2);
      });

      it('should correctly identify paginated response with results key', async () => {
        const mockHaunts: Haunt[] = [
          {
            id: '1',
            owner: 'user1',
            name: 'Test Haunt',
            url: 'https://example.com',
            description: 'Test description',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'once',
            scrape_interval: 3600,
            is_public: false,
            public_slug: null,
            folder: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];

        // Mock response with pagination metadata
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            count: 1,
            next: null,
            previous: null,
            results: mockHaunts,
          }),
        });

        const result = await apiClient.getHaunts();

        expect(result).toEqual(mockHaunts);
        expect(result).not.toHaveProperty('count');
        expect(result).not.toHaveProperty('next');
      });
    });

    describe('getHaunt', () => {
      it('should fetch a single haunt by id', async () => {
        const mockHaunt: Haunt = {
          id: '1',
          owner: 'user1',
          name: 'Test Haunt',
          url: 'https://example.com',
          description: 'Test description',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once',
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHaunt,
        });

        const result = await apiClient.getHaunt('1');

        expect(result).toEqual(mockHaunt);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/1/'),
          expect.any(Object)
        );
      });
    });

    describe('createHaunt', () => {
      it('should create a new haunt', async () => {
        const createRequest: CreateHauntRequest = {
          name: 'New Haunt',
          url: 'https://example.com',
          description: 'Monitor price changes',
          scrape_interval: 3600,
          alert_mode: 'on_change',
          is_public: false,
        };

        const mockHaunt: Haunt = {
          id: '2',
          owner: 'user1',
          ...createRequest,
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          public_slug: null,
          folder: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHaunt,
        });

        const result = await apiClient.createHaunt(createRequest);

        expect(result).toEqual(mockHaunt);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify(createRequest),
          })
        );
      });
    });

    describe('updateHaunt', () => {
      it('should update an existing haunt', async () => {
        const updateData = { name: 'Updated Name' };
        const mockHaunt: Haunt = {
          id: '1',
          owner: 'user1',
          name: 'Updated Name',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once',
          scrape_interval: 3600,
          is_public: false,
          public_slug: null,
          folder: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHaunt,
        });

        const result = await apiClient.updateHaunt('1', updateData);

        expect(result).toEqual(mockHaunt);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/1/'),
          expect.objectContaining({
            method: 'PUT',
            body: JSON.stringify(updateData),
          })
        );
      });
    });

    describe('deleteHaunt', () => {
      it('should delete a haunt', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

        await apiClient.deleteHaunt('1');

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/1/'),
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });

    describe('makeHauntPublic', () => {
      it('should make a haunt public', async () => {
        const mockHaunt: Haunt = {
          id: '1',
          owner: 'user1',
          name: 'Test Haunt',
          url: 'https://example.com',
          description: 'Test',
          config: { selectors: {}, normalization: {}, truthy_values: {} },
          current_state: {},
          last_alert_state: null,
          alert_mode: 'once',
          scrape_interval: 3600,
          is_public: true,
          public_slug: 'test-haunt',
          folder: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHaunt,
        });

        const result = await apiClient.makeHauntPublic('1');

        expect(result.is_public).toBe(true);
        expect(result.public_slug).toBe('test-haunt');
      });
    });

    describe('testScrape', () => {
      it('should test scrape configuration', async () => {
        const testRequest: TestScrapeRequest = {
          url: 'https://example.com',
          description: 'Monitor price',
        };

        const mockResponse: TestScrapeResponse = {
          config: {
            selectors: { price: '.price' },
            normalization: {},
            truthy_values: {},
          },
          extracted_data: { price: '$99.99' },
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const result = await apiClient.testScrape(testRequest);

        expect(result).toEqual(mockResponse);
      });
    });

    describe('refreshHaunt', () => {
      it('should trigger manual refresh', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

        await apiClient.refreshHaunt('1');

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/haunts/1/refresh/'),
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });

    describe('getPublicHaunts', () => {
      it('should fetch public haunts with paginated response', async () => {
        const mockHaunts: Haunt[] = [
          {
            id: '1',
            owner: 'user1',
            name: 'Public Haunt',
            url: 'https://example.com',
            description: 'Test',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'once',
            scrape_interval: 3600,
            is_public: true,
            public_slug: 'public-haunt',
            folder: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ results: mockHaunts }),
        });

        const result = await apiClient.getPublicHaunts();

        expect(result).toEqual(mockHaunts);
      });

      it('should handle non-paginated response', async () => {
        const mockHaunts: Haunt[] = [
          {
            id: '1',
            owner: 'user1',
            name: 'Public Haunt',
            url: 'https://example.com',
            description: 'Test',
            config: { selectors: {}, normalization: {}, truthy_values: {} },
            current_state: {},
            last_alert_state: null,
            alert_mode: 'once',
            scrape_interval: 3600,
            is_public: true,
            public_slug: 'public-haunt',
            folder: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHaunts,
        });

        const result = await apiClient.getPublicHaunts();

        expect(result).toEqual(mockHaunts);
      });
    });
  });

  describe('Folders', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('getFolders', () => {
      it('should fetch all folders', async () => {
        const mockFolders: Folder[] = [
          {
            id: '1',
            name: 'Work',
            parent: null,
            user: 'user1',
            created_at: '2024-01-01T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockFolders,
        });

        const result = await apiClient.getFolders();

        expect(result).toEqual(mockFolders);
      });
    });

    describe('createFolder', () => {
      it('should create a new folder', async () => {
        const mockFolder: Folder = {
          id: '2',
          name: 'Personal',
          parent: null,
          user: 'user1',
          created_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockFolder,
        });

        const result = await apiClient.createFolder('Personal');

        expect(result).toEqual(mockFolder);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/folders/'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ name: 'Personal', parent: null }),
          })
        );
      });

      it('should create a nested folder', async () => {
        const mockFolder: Folder = {
          id: '3',
          name: 'Subfolder',
          parent: '1',
          user: 'user1',
          created_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockFolder,
        });

        const result = await apiClient.createFolder('Subfolder', '1');

        expect(result.parent).toBe('1');
      });
    });

    describe('updateFolder', () => {
      it('should update a folder', async () => {
        const mockFolder: Folder = {
          id: '1',
          name: 'Updated Name',
          parent: null,
          user: 'user1',
          created_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockFolder,
        });

        const result = await apiClient.updateFolder('1', { name: 'Updated Name' });

        expect(result.name).toBe('Updated Name');
      });
    });

    describe('deleteFolder', () => {
      it('should delete a folder', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

        await apiClient.deleteFolder('1');

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/folders/1/'),
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });
  });

  describe('RSS Items', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('getRSSItems', () => {
      it('should fetch all RSS items', async () => {
        const mockItems: RSSItem[] = [
          {
            id: '1',
            haunt: 'haunt1',
            title: 'Change Detected',
            description: 'Price changed',
            link: 'https://example.com',
            pub_date: '2024-01-01T00:00:00Z',
            guid: 'guid1',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockItems,
        });

        const result = await apiClient.getRSSItems();

        expect(result).toEqual(mockItems);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/rss/items/'),
          expect.any(Object)
        );
      });

      it('should fetch RSS items for specific haunt', async () => {
        const mockItems: RSSItem[] = [
          {
            id: '1',
            haunt: 'haunt1',
            title: 'Change Detected',
            description: 'Price changed',
            link: 'https://example.com',
            pub_date: '2024-01-01T00:00:00Z',
            guid: 'guid1',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockItems,
        });

        const result = await apiClient.getRSSItems('haunt1');

        expect(result).toEqual(mockItems);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/rss/items/?haunt=haunt1'),
          expect.any(Object)
        );
      });
    });

    describe('getRSSItem', () => {
      it('should fetch a single RSS item', async () => {
        const mockItem: RSSItem = {
          id: '1',
          haunt: 'haunt1',
          title: 'Change Detected',
          description: 'Price changed',
          link: 'https://example.com',
          pub_date: '2024-01-01T00:00:00Z',
          guid: 'guid1',
          ai_summary: 'AI generated summary',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockItem,
        });

        const result = await apiClient.getRSSItem('1');

        expect(result).toEqual(mockItem);
      });
    });
  });

  describe('Subscriptions', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('getSubscriptions', () => {
      it('should fetch all subscriptions', async () => {
        const mockSubscriptions: Subscription[] = [
          {
            id: '1',
            user: 'user1',
            haunt: 'haunt1',
            subscribed_at: '2024-01-01T00:00:00Z',
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockSubscriptions,
        });

        const result = await apiClient.getSubscriptions();

        expect(result).toEqual(mockSubscriptions);
      });
    });

    describe('subscribe', () => {
      it('should subscribe to a haunt', async () => {
        const mockSubscription: Subscription = {
          id: '2',
          user: 'user1',
          haunt: 'haunt2',
          subscribed_at: '2024-01-01T00:00:00Z',
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockSubscription,
        });

        const result = await apiClient.subscribe('haunt2');

        expect(result).toEqual(mockSubscription);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/subscriptions/'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ haunt_id: 'haunt2' }),
          })
        );
      });
    });

    describe('unsubscribe', () => {
      it('should unsubscribe from a haunt', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

        await apiClient.unsubscribe('1');

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/subscriptions/1/'),
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });
  });

  describe('Read States', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('getReadStates', () => {
      it('should fetch all read states', async () => {
        const mockStates: UserReadState[] = [
          {
            id: '1',
            user: 'user1',
            rss_item: 'item1',
            is_read: true,
            is_starred: false,
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockStates,
        });

        const result = await apiClient.getReadStates();

        expect(result).toEqual(mockStates);
      });

      it('should fetch read states for specific haunt', async () => {
        const mockStates: UserReadState[] = [
          {
            id: '1',
            user: 'user1',
            rss_item: 'item1',
            is_read: true,
            is_starred: false,
          },
        ];

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockStates,
        });

        const result = await apiClient.getReadStates('haunt1');

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/read-states/?haunt=haunt1'),
          expect.any(Object)
        );
      });
    });

    describe('markAsRead', () => {
      it('should mark item as read', async () => {
        const mockState: UserReadState = {
          id: '1',
          user: 'user1',
          rss_item: 'item1',
          is_read: true,
          is_starred: false,
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockState,
        });

        const result = await apiClient.markAsRead('item1');

        expect(result.is_read).toBe(true);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/read-states/item1/mark-read/'),
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });

    describe('markAsUnread', () => {
      it('should mark item as unread', async () => {
        const mockState: UserReadState = {
          id: '1',
          user: 'user1',
          rss_item: 'item1',
          is_read: false,
          is_starred: false,
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockState,
        });

        const result = await apiClient.markAsUnread('item1');

        expect(result.is_read).toBe(false);
      });
    });

    describe('toggleStar', () => {
      it('should toggle star status', async () => {
        const mockState: UserReadState = {
          id: '1',
          user: 'user1',
          rss_item: 'item1',
          is_read: true,
          is_starred: true,
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockState,
        });

        const result = await apiClient.toggleStar('item1');

        expect(result.is_starred).toBe(true);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/read-states/item1/toggle-star/'),
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });

    describe('bulkMarkAsRead', () => {
      it('should mark multiple items as read', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

        await apiClient.bulkMarkAsRead(['item1', 'item2', 'item3']);

        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/read-states/bulk-mark-read/'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ item_ids: ['item1', 'item2', 'item3'] }),
          })
        );
      });
    });
  });

  describe('User Preferences', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('getUserPreferences', () => {
      it('should fetch user preferences', async () => {
        const mockPreferences: UserUIPreferences = {
          left_panel_width: 280,
          middle_panel_width: 400,
          keyboard_shortcuts_enabled: true,
          auto_mark_read_on_scroll: false,
          collapsed_folders: ['folder1', 'folder2'],
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockPreferences,
        });

        const result = await apiClient.getUserPreferences();

        expect(result).toEqual(mockPreferences);
      });
    });

    describe('updateUserPreferences', () => {
      it('should update user preferences', async () => {
        const updateData = {
          keyboard_shortcuts_enabled: false,
          collapsed_folders: ['folder1'],
        };

        const mockPreferences: UserUIPreferences = {
          left_panel_width: 280,
          middle_panel_width: 400,
          keyboard_shortcuts_enabled: false,
          auto_mark_read_on_scroll: false,
          collapsed_folders: ['folder1'],
        };

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockPreferences,
        });

        const result = await apiClient.updateUserPreferences(updateData);

        expect(result.keyboard_shortcuts_enabled).toBe(false);
        expect(result.collapsed_folders).toEqual(['folder1']);
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/user/preferences/'),
          expect.objectContaining({
            method: 'PUT',
            body: JSON.stringify(updateData),
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      localStorageMock.setItem('accessToken', 'token');
    });

    describe('401 Unauthorized', () => {
      it('should clear token and redirect on 401 error', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Token expired' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(localStorageMock.removeItem).toHaveBeenCalledWith('accessToken');
        expect(window.location.href).toBe('/login');
      });

      it('should extract error message from detail field for logging', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Token has expired' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'Token has expired',
            tokenWasPresent: true,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should extract error message from nested error.message field', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ error: { message: 'Authentication failed' } }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'Authentication failed',
            tokenWasPresent: true,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should extract error message from message field', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        localStorageMock.setItem('accessToken', 'test-token');
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ message: 'Unauthorized access' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'Unauthorized access',
            tokenWasPresent: true,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should use default message when no error detail is available', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        localStorageMock.setItem('accessToken', 'test-token');
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({}),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'No error detail',
            tokenWasPresent: true,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should log token presence correctly when token exists', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        localStorageMock.setItem('accessToken', 'valid-token');
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Invalid token' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            tokenWasPresent: true,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should log token presence correctly when token is missing', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        localStorageMock.clear();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'No token provided' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            tokenWasPresent: false,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should include endpoint in error log', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Unauthorized' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            endpoint: '/haunts/',
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should include retry count in error log', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Unauthorized' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            retryCount: 0,
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should handle malformed JSON in 401 response', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        localStorageMock.setItem('accessToken', 'test-token');
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => {
            throw new Error('Invalid JSON');
          },
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'Request failed',
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should prioritize detail over error.message', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ 
            detail: 'Primary error message',
            error: { message: 'Secondary error message' }
          }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'Primary error message',
          })
        );

        consoleErrorSpy.mockRestore();
      });

      it('should prioritize error.message over message', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ 
            error: { message: 'Nested error message' },
            message: 'Top-level message'
          }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow();

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          '[API Client] 401 Unauthorized:',
          expect.objectContaining({
            error: 'Nested error message',
          })
        );

        consoleErrorSpy.mockRestore();
      });
    });

    describe('Network Errors', () => {
      it('should handle network errors', async () => {
        (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

        await expect(apiClient.getHaunts()).rejects.toThrow('Network error');
      });
    });

    describe('Server Errors', () => {
      it('should handle 500 errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ detail: 'Internal server error' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Internal server error');
      });

      it('should handle errors without detail field', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({}),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('HTTP 400');
      });

      it('should handle malformed JSON responses', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => {
            throw new Error('Invalid JSON');
          },
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Request failed');
      });

      it('should extract error message from detail field for non-401 errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Bad request error' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Bad request error');
      });

      it('should extract error message from error.message field for non-401 errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ error: { message: 'Validation failed' } }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Validation failed');
      });

      it('should extract error message from message field for non-401 errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ message: 'Request error' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Request error');
      });

      it('should use HTTP status code when no error message available', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 403,
          json: async () => ({}),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('HTTP 403');
      });

      it('should handle validation errors with field details', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ 
            error: { 
              details: {
                email: ['This field is required'],
                password: ['Password is too short']
              }
            }
          }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('email: This field is required; password: Password is too short');
      });

      it('should handle validation errors with single field error', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ 
            error: { 
              details: {
                username: ['Username already exists']
              }
            }
          }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('username: Username already exists');
      });

      it('should handle validation errors with non-array messages', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ 
            error: { 
              details: {
                name: 'Name is required'
              }
            }
          }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('name: Name is required');
      });

      it('should fallback to detail when validation details are empty', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ 
            detail: 'Validation failed',
            error: { 
              details: {}
            }
          }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Validation failed');
      });

      it('should handle 404 errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 404,
          json: async () => ({ detail: 'Not found' }),
        });

        await expect(apiClient.getHaunt('999')).rejects.toThrow('Not found');
      });

      it('should handle 403 forbidden errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 403,
          json: async () => ({ detail: 'Permission denied' }),
        });

        await expect(apiClient.deleteHaunt('1')).rejects.toThrow('Permission denied');
      });

      it('should handle 429 rate limit errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 429,
          json: async () => ({ detail: 'Too many requests' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Too many requests');
      });

      it('should handle 503 service unavailable errors', async () => {
        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 503,
          json: async () => ({ detail: 'Service temporarily unavailable' }),
        });

        await expect(apiClient.getHaunts()).rejects.toThrow('Service temporarily unavailable');
      });
    });
  });

  describe('Token Management', () => {
    describe('setAccessToken', () => {
      it('should store token in localStorage', () => {
        apiClient.setAccessToken('new-token');

        expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'new-token');
      });

      it('should remove token from localStorage when null', () => {
        apiClient.setAccessToken(null);

        expect(localStorageMock.removeItem).toHaveBeenCalledWith('accessToken');
      });
    });

    describe('Token Synchronization', () => {
      it('should sync token from localStorage on each request', async () => {
        localStorageMock.clear();
        localStorageMock.setItem('accessToken', 'stored-token');

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ results: [] }),
        });

        await apiClient.getHaunts();

        expect(fetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer stored-token',
            }),
          })
        );
      });

      it('should not include Authorization header when no token', async () => {
        localStorageMock.clear();

        (fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        });

        await apiClient.getHaunts();

        const callArgs = (fetch as jest.Mock).mock.calls[0];
        const headers = callArgs[1].headers;
        expect(headers.Authorization).toBeUndefined();
      });
    });
  });
});
