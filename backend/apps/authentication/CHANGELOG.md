# Authentication API Changelog

## [Recent] - Response Structure Update

### Changed
- **Registration endpoint** (`POST /api/v1/auth/register/`): Token response structure flattened
  - **Before**: `{ user: {...}, tokens: { refresh: "...", access: "..." } }`
  - **After**: `{ user: {...}, refresh: "...", access: "..." }`

- **Login endpoint** (`POST /api/v1/auth/login/`): Token response structure flattened
  - **Before**: `{ user: {...}, tokens: { refresh: "...", access: "..." } }`
  - **After**: `{ user: {...}, refresh: "...", access: "..." }`

### Impact
- Frontend code already compatible with new structure
- Simplifies response parsing by removing unnecessary nesting
- No breaking changes for existing clients that access tokens directly from response root

### Migration Guide
If you have existing API clients, update token access:
```javascript
// Old way
const accessToken = response.data.tokens.access;
const refreshToken = response.data.tokens.refresh;

// New way
const accessToken = response.data.access;
const refreshToken = response.data.refresh;
```
