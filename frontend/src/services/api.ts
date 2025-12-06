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

// Use relative URL in production (empty env var), absolute URL in development
const API_BASE_URL = process.env.REACT_APP_API_URL 
  ? process.env.REACT_APP_API_URL  // Use provided URL (dev or custom)
  : '/api/v1';  // Production default: relative URL (same origin)

class APIClient {
  private baseURL: string;
  private accessToken: string | null = null;
  private refreshPromise: Promise<string> | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    // Load token from localStorage on initialization
    this.accessToken = localStorage.getItem('accessToken');
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      localStorage.setItem('accessToken', token);
    } else {
      localStorage.removeItem('accessToken');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Always check localStorage for the latest token FIRST
    const token = localStorage.getItem('accessToken');
    
    // Build headers with token if available
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      // Sync in-memory token with localStorage
      if (this.accessToken !== token) {
        this.accessToken = token;
      }
    } else {
      // Clear in-memory token if localStorage is empty
      this.accessToken = null;
    }

    console.log('[API Client] Making request to:', endpoint);
    console.log('[API Client] Token present:', !!token);
    console.log('[API Client] Authorization header:', headers['Authorization'] ? 'set' : 'missing');

    const response = await fetch(url, {
      ...options,
      headers,
      mode: 'cors',
      credentials: 'include', // Ensure cookies are sent if needed
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      
      if (response.status === 401) {
        // Extract error message for logging
        const errorMsg = error.detail || error.error?.message || error.message || 'No error detail';
        
        console.error('[API Client] 401 Unauthorized:', {
          endpoint,
          tokenWasPresent: !!token,
          error: errorMsg,
          retryCount
        });
        
        // If token was present and this is the first attempt, try to refresh the token
        if (token && retryCount === 0 && !endpoint.includes('/auth/')) {
          console.log('[API Client] Attempting to refresh token...');
          
          // If a refresh is already in progress, wait for it
          if (this.refreshPromise) {
            console.log('[API Client] Refresh already in progress, waiting...');
            try {
              await this.refreshPromise;
              console.log('[API Client] Refresh completed, retrying request...');
              return this.request<T>(endpoint, options, retryCount + 1);
            } catch (refreshError) {
              console.error('[API Client] Refresh failed, logging out');
              this.setAccessToken(null);
              localStorage.removeItem('refreshToken');
              window.location.href = '/login';
              throw new Error('Authentication failed');
            }
          }
          
          // Start a new refresh
          this.refreshPromise = (async () => {
            try {
              const refreshToken = localStorage.getItem('refreshToken');
              if (!refreshToken) {
                throw new Error('No refresh token available');
              }
              
              const refreshResponse = await fetch(`${this.baseURL}/auth/refresh/`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
                mode: 'cors',
                credentials: 'include',
              });
              
              if (!refreshResponse.ok) {
                const errorData = await refreshResponse.json().catch(() => ({}));
                console.error('[API Client] Token refresh failed:', errorData);
                throw new Error('Token refresh failed');
              }
              
              const refreshData = await refreshResponse.json();
              this.setAccessToken(refreshData.access);
              console.log('[API Client] Token refreshed successfully');
              return refreshData.access;
            } finally {
              this.refreshPromise = null;
            }
          })();
          
          try {
            await this.refreshPromise;
            console.log('[API Client] Retrying request with new token...');
            return this.request<T>(endpoint, options, retryCount + 1);
          } catch (refreshError) {
            console.error('[API Client] Token refresh failed, logging out');
            this.setAccessToken(null);
            localStorage.removeItem('refreshToken');
            window.location.href = '/login';
            throw new Error('Authentication failed');
          }
        }
        
        // If we get here with a 401, it means:
        // 1. No token was present initially, OR
        // 2. This is an auth endpoint, OR
        // 3. Token refresh already failed (retryCount > 0)
        console.log('[API Client] Clearing token and redirecting to login');
        this.setAccessToken(null);
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
      
      // Extract error message from various response formats
      const errorMessage = error.detail || error.error?.message || error.message || `HTTP ${response.status}`;
      
      // For validation errors, extract field-specific messages
      if (error.error?.details) {
        const details = error.error.details;
        if (typeof details === 'object') {
          // Flatten validation errors into a readable message
          const fieldErrors = Object.entries(details)
            .map(([field, messages]) => {
              if (Array.isArray(messages)) {
                return `${field}: ${messages.join(', ')}`;
              }
              return `${field}: ${messages}`;
            })
            .join('; ');
          throw new Error(fieldErrors || errorMessage);
        }
      }
      
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    console.log('[API Client] Logging in with:', credentials.email);
    const response = await this.request<LoginResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    console.log('[API Client] Login response:', {
      hasUser: !!response.user,
      hasAccess: !!response.access,
      hasRefresh: !!response.refresh,
      accessToken: response.access ? `${response.access.substring(0, 20)}...` : 'NULL',
    });
    this.setAccessToken(response.access);
    localStorage.setItem('refreshToken', response.refresh);
    return response;
  }

  async register(userData: {
    email: string;
    username: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
  }): Promise<LoginResponse> {
    console.log('[API Client] Registering user:', userData.email);
    const response = await this.request<LoginResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    console.log('[API Client] Registration response:', {
      hasUser: !!response.user,
      hasAccess: !!response.access,
      hasRefresh: !!response.refresh,
    });
    this.setAccessToken(response.access);
    localStorage.setItem('refreshToken', response.refresh);
    return response;
  }

  async logout(): Promise<void> {
    this.setAccessToken(null);
    localStorage.removeItem('refreshToken');
  }

  async refreshToken(): Promise<{ access: string }> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await this.request<{ access: string }>('/auth/refresh/', {
      method: 'POST',
      body: JSON.stringify({ refresh: refreshToken }),
    });
    this.setAccessToken(response.access);
    return response;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/profile/');
  }

  // Haunts
  async getHaunts(): Promise<Haunt[]> {
    const response = await this.request<{ results: Haunt[] } | Haunt[]>('/haunts/');
    // Handle paginated response
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle non-paginated response (fallback)
    return response as Haunt[];
  }

  async getHaunt(id: string): Promise<Haunt> {
    return this.request<Haunt>(`/haunts/${id}/`);
  }

  async createHaunt(data: CreateHauntRequest): Promise<Haunt> {
    return this.request<Haunt>('/haunts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateHaunt(id: string, data: Partial<Haunt>): Promise<Haunt> {
    return this.request<Haunt>(`/haunts/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteHaunt(id: string): Promise<void> {
    await this.request<void>(`/haunts/${id}/`, {
      method: 'DELETE',
    });
  }

  async makeHauntPublic(id: string): Promise<Haunt> {
    return this.request<Haunt>(`/haunts/${id}/make-public/`, {
      method: 'POST',
    });
  }

  async testScrape(data: TestScrapeRequest): Promise<TestScrapeResponse> {
    console.log('[API Client] testScrape called with data:', data);
    console.log('[API Client] Current token in localStorage:', localStorage.getItem('accessToken') ? 'present' : 'missing');
    console.log('[API Client] Current token in memory:', this.accessToken ? 'present' : 'missing');
    return this.request<TestScrapeResponse>('/haunts/generate-config-preview/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async testScrapeWithConfig(url: string, config: any): Promise<any> {
    return this.request<any>('/haunts/test-scrape/', {
      method: 'POST',
      body: JSON.stringify({ url, config }),
    });
  }

  async refreshHaunt(id: string): Promise<void> {
    await this.request<void>(`/haunts/${id}/refresh/`, {
      method: 'POST',
    });
  }

  // Folders
  async getFolders(): Promise<Folder[]> {
    const response = await this.request<{ results: Folder[] } | Folder[]>('/folders/');
    // Handle paginated response
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle non-paginated response (fallback)
    return response as Folder[];
  }

  async createFolder(name: string, parent: string | null = null): Promise<Folder> {
    return this.request<Folder>('/folders/', {
      method: 'POST',
      body: JSON.stringify({ name, parent }),
    });
  }

  async updateFolder(id: string, data: Partial<Folder>): Promise<Folder> {
    return this.request<Folder>(`/folders/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteFolder(id: string): Promise<void> {
    await this.request<void>(`/folders/${id}/`, {
      method: 'DELETE',
    });
  }

  // RSS Items
  async getRSSItems(hauntId?: string): Promise<RSSItem[]> {
    const endpoint = hauntId ? `/rss/items/?haunt=${hauntId}` : '/rss/items/';
    const response = await this.request<{ results: RSSItem[] } | RSSItem[]>(endpoint);
    // Handle paginated response
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle non-paginated response (fallback)
    return response as RSSItem[];
  }

  async getRSSItem(id: string): Promise<RSSItem> {
    return this.request<RSSItem>(`/rss/items/${id}/`);
  }

  // Subscriptions
  async getSubscriptions(): Promise<Subscription[]> {
    const response = await this.request<{ results: Subscription[] } | Subscription[]>('/subscriptions/');
    // Handle paginated response
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle non-paginated response (fallback)
    return response as Subscription[];
  }

  async subscribe(hauntId: string): Promise<Subscription> {
    return this.request<Subscription>('/subscriptions/', {
      method: 'POST',
      body: JSON.stringify({ haunt_id: hauntId }),
    });
  }

  async unsubscribe(subscriptionId: string): Promise<void> {
    await this.request<void>(`/subscriptions/${subscriptionId}/`, {
      method: 'DELETE',
    });
  }

  async getPublicHaunts(): Promise<Haunt[]> {
    const response = await this.request<{ results: Haunt[] } | Haunt[]>('/haunts/public/');
    // Handle paginated response
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle non-paginated response (fallback)
    return response as Haunt[];
  }

  // Read States
  async getReadStates(hauntId?: string): Promise<UserReadState[]> {
    const endpoint = hauntId ? `/read-states/?haunt=${hauntId}` : '/read-states/';
    const response = await this.request<{ results: UserReadState[] } | UserReadState[]>(endpoint);
    // Handle paginated response
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle non-paginated response (fallback)
    return response as UserReadState[];
  }

  async markAsRead(itemId: string): Promise<UserReadState> {
    return this.request<UserReadState>(`/read-states/${itemId}/mark-read/`, {
      method: 'POST',
    });
  }

  async markAsUnread(itemId: string): Promise<UserReadState> {
    return this.request<UserReadState>(`/read-states/${itemId}/mark-unread/`, {
      method: 'POST',
    });
  }

  async toggleStar(itemId: string): Promise<UserReadState> {
    return this.request<UserReadState>(`/read-states/${itemId}/toggle-star/`, {
      method: 'POST',
    });
  }

  async bulkMarkAsRead(itemIds: string[]): Promise<void> {
    await this.request<void>('/read-states/bulk-mark-read/', {
      method: 'POST',
      body: JSON.stringify({ item_ids: itemIds }),
    });
  }

  // User Preferences
  async getUserPreferences(): Promise<UserUIPreferences> {
    return this.request<UserUIPreferences>('/user/preferences/');
  }

  async updateUserPreferences(data: Partial<UserUIPreferences>): Promise<UserUIPreferences> {
    return this.request<UserUIPreferences>('/user/preferences/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new APIClient(API_BASE_URL);
export default apiClient;
