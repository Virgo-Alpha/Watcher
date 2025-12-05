// Core domain types
export interface User {
  id: string;
  email: string;
  username: string;
}

export interface Folder {
  id: string;
  name: string;
  parent: string | null;
  user: string;
  created_at: string;
}

export interface HauntConfig {
  selectors: Record<string, string>;
  normalization: Record<string, {
    type: string;
    transform?: string;
  }>;
  truthy_values: Record<string, string[]>;
}

export interface Haunt {
  id: string;
  owner: string;
  name: string;
  url: string;
  description: string;
  config: HauntConfig;
  current_state: Record<string, any>;
  last_alert_state: Record<string, any> | null;
  alert_mode: 'once' | 'on_change';
  scrape_interval: number;
  is_public: boolean;
  public_slug: string | null;
  folder: string | null;
  is_active: boolean;
  last_scraped_at: string | null;
  last_error: string;
  error_count: number;
  enable_ai_summary: boolean;
  created_at: string;
  updated_at: string;
  unread_count?: number;
}

export interface RSSItem {
  id: string;
  haunt: string;
  title: string;
  description: string;
  link: string;
  pub_date: string;
  guid: string;
  ai_summary?: string;
}

export interface Subscription {
  id: string;
  user: string;
  haunt: string;
  subscribed_at: string;
}

export interface UserReadState {
  id: string;
  user: string;
  rss_item: string;
  is_read: boolean;
  is_starred: boolean;
}

export interface UserUIPreferences {
  left_panel_width: number;
  middle_panel_width: number;
  keyboard_shortcuts_enabled: boolean;
  auto_mark_read_on_scroll: boolean;
  collapsed_folders: string[];
}

// API request/response types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface CreateHauntRequest {
  name: string;
  url: string;
  description: string;
  folder?: string | null;
  scrape_interval: number;
  alert_mode: 'once' | 'on_change';
  is_public: boolean;
}

export interface TestScrapeRequest {
  url: string;
  description: string;
}

export interface TestScrapeResponse {
  config: HauntConfig;
  extracted_data: Record<string, any>;
}

// UI state types
export interface FolderTree extends Folder {
  children: FolderTree[];
  haunts: Haunt[];
  unread_count: number;
  is_expanded: boolean;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface HauntsState {
  items: Haunt[];
  folders: Folder[];
  selectedHaunt: Haunt | null;
  loading: boolean;
  error: string | null;
}

export interface RSSItemsState {
  items: RSSItem[];
  selectedItem: RSSItem | null;
  unreadCounts: Record<string, number>;
  readStates: Record<string, UserReadState>;
  loading: boolean;
  error: string | null;
}

export interface UIState {
  leftPanelWidth: number;
  middlePanelWidth: number;
  showSetupWizard: boolean;
  keyboardShortcutsEnabled: boolean;
  autoMarkReadOnScroll: boolean;
  collapsedFolders: string[];
}

export interface AppState {
  auth: AuthState;
  haunts: HauntsState;
  rssItems: RSSItemsState;
  ui: UIState;
}
