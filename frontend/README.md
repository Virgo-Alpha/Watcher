# Watcher Frontend

React-based frontend for the Watcher site change monitoring application.

## Structure

```
src/
├── components/          # Reusable UI components
│   └── auth/           # Authentication components
├── pages/              # Route-level page components
├── store/              # Redux store and slices
│   └── slices/         # Redux Toolkit slices
├── services/           # API client and business logic
├── hooks/              # Custom React hooks
├── utils/              # Utility functions
└── types/              # TypeScript type definitions
```

## Key Features

- **Redux State Management**: Centralized state with Redux Toolkit
  - `auth`: User authentication and session management
  - `haunts`: Haunt and folder management
  - `rssItems`: RSS items and read states
  - `ui`: UI preferences and panel widths

- **API Client**: Centralized API communication with automatic token management
- **Protected Routes**: Authentication-based route protection
- **TypeScript**: Full type safety across the application

## Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Docker Development

The frontend runs in a Docker container with hot reload support:

```bash
# Start all services including frontend
docker-compose up

# View frontend logs
docker-compose logs -f frontend

# Rebuild frontend container
docker-compose build frontend
```

The frontend is accessible at http://localhost:3000 and proxies API requests to the backend at http://localhost:8000.

## Environment Variables

- `REACT_APP_API_URL`: Backend API URL configuration
  - **Development**: Set to `http://localhost:8000/api/v1` for local backend
  - **Production**: Leave undefined or set to empty string to use relative URLs (`/api/v1`)
  - The frontend automatically detects the environment and uses the appropriate URL
- `CHOKIDAR_USEPOLLING`: Enable file watching in Docker (set to true)

## State Management

### Auth State
- User authentication status
- JWT token management
- Current user information

### Haunts State
- List of user's haunts
- Folder hierarchy
- Selected haunt

### RSS Items State
- RSS feed items
- Read/unread states
- Star states
- Unread counts per haunt

### UI State
- Panel widths (resizable)
- Collapsed folders
- Keyboard shortcuts enabled
- Auto-mark-as-read preferences

## API Client

The API client (`src/services/api.ts`) provides methods for:
- Authentication (login, logout, token refresh)
- Haunt management (CRUD operations)
- Folder management
- RSS item retrieval
- Read state management
- User preferences

All API calls automatically include authentication tokens and handle token expiration.
