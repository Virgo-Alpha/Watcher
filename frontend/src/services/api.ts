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

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class APIClient {
  private baseURL: string;
  private accessToken: string | null = null;

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
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        this.setAccessToken(null);
        window.location.href = '/login';
      }
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
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
    return this.request<User>('/auth/user/');
  }

  // Haunts
  async getHaunts(): Promise<Haunt[]> {
    return this.request<Haunt[]>('/haunts/');
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
    return this.request<TestScrapeResponse>('/haunts/test-scrape/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async refreshHaunt(id: string): Promise<void> {
    await this.request<void>(`/haunts/${id}/refresh/`, {
      method: 'POST',
    });
  }

  // Folders
  async getFolders(): Promise<Folder[]> {
    return this.request<Folder[]>('/folders/');
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
    return this.request<RSSItem[]>(endpoint);
  }

  async getRSSItem(id: string): Promise<RSSItem> {
    return this.request<RSSItem>(`/rss/items/${id}/`);
  }

  // Subscriptions
  async getSubscriptions(): Promise<Subscription[]> {
    return this.request<Subscription[]>('/subscriptions/');
  }

  async subscribe(hauntId: string): Promise<Subscription> {
    return this.request<Subscription>('/subscriptions/', {
      method: 'POST',
      body: JSON.stringify({ haunt: hauntId }),
    });
  }

  async unsubscribe(subscriptionId: string): Promise<void> {
    await this.request<void>(`/subscriptions/${subscriptionId}/`, {
      method: 'DELETE',
    });
  }

  async getPublicHaunts(): Promise<Haunt[]> {
    return this.request<Haunt[]>('/haunts/public/');
  }

  // Read States
  async getReadStates(hauntId?: string): Promise<UserReadState[]> {
    const endpoint = hauntId ? `/read-states/?haunt=${hauntId}` : '/read-states/';
    return this.request<UserReadState[]>(endpoint);
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
