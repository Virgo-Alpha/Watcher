# Implementation Plan

- [x] 1. Set up Docker containerized project structure

  - [x] 1.1 Create Docker Compose configuration

    - Create docker-compose.yml with services for web, db, redis, celery, scheduler
    - Create Dockerfile for Django application with Playwright dependencies
    - Add environment variable configuration for different environments
    - Create .dockerignore and docker-related configuration files
    - _Requirements: All requirements depend on basic project setup_

  - [x] 1.2 Initialize Django project with dependencies
    - Create Django project with required packages (Django, DRF, Celery, Redis, Playwright, psycopg2)
    - Configure settings for containerized development and production environments
    - Set up database configuration for PostgreSQL container
    - Create requirements.txt with all Python dependencies
    - _Requirements: All requirements depend on basic project setup_

- [x] 2. Implement core data models

  - [x] 2.1 Create User authentication models and configuration

    - Implement Django User model extensions if needed
    - Configure authentication backends and JWT settings
    - Create user registration and login serializers
    - _Requirements: 8.1, 9.1, 9.2, 9.3_

  - [x] 2.2 Create Haunt model with all required fields

    - Implement Haunt model with UUID primary key, owner, config JSONField, state tracking
    - Add model validation for scrape intervals and alert modes
    - Create database migrations for Haunt model
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 5.1, 5.2, 6.1, 8.1, 8.2_

  - [x] 2.3 Create folder organization models

    - Implement Folder model with hierarchical structure and user ownership
    - Add folder field to Haunt model with foreign key relationship
    - Create UserUIPreferences model for storing panel widths and UI settings
    - Create database migrations for folder and UI preference models
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 2.4 Create RSS and subscription models
    - Implement RSSItem model with haunt relationship and feed data
    - Create Subscription model for public haunt subscriptions
    - Implement UserReadState model for read/star tracking
    - Create database migrations for RSS and subscription models
    - _Requirements: 7.1, 7.2, 8.3, 9.1, 9.2, 9.3_

- [x] 3. Implement AI configuration service

  - [x] 3.1 Create LLM integration service

    - ✅ Implement AIConfigService class with OpenAI API client
    - ✅ Create configuration generation method from natural language
    - ✅ Add configuration validation and error handling
    - ✅ Add OpenAI dependency to requirements.txt
    - Write unit tests for AI service methods
    - _Requirements: 1.1, 1.2, 10.1, 10.2, 10.3, 10.4_

  - [x] 3.2 Implement configuration schema and validation
    - Define JSON schema for haunt configurations (selectors, normalization, truthy values)
    - Create validation functions for generated configurations
    - Implement configuration parsing and storage utilities
    - Write unit tests for configuration validation
    - _Requirements: 2.1, 2.2, 10.2, 10.3, 10.4_

- [x] 4. Build haunt management API

  - [x] 4.1 Create folder management endpoints

    - Implement FolderViewSet with CRUD operations for folder hierarchy
    - Add folder tree retrieval endpoint with nested structure
    - Create folder assignment endpoints for organizing haunts
    - Write API tests for folder operations and hierarchy management
    - _Requirements: 13.1, 13.2, 13.3, 13.5_

  - [x] 4.2 Create haunt CRUD endpoints with folder support

    - Implement HauntViewSet with create, list, retrieve, update, delete actions
    - Add permission classes for owner-only access to private haunts
    - Create haunt serializers with nested configuration and folder handling
    - Add unread count calculation for haunts and folders
    - Write API tests for haunt CRUD operations
    - _Requirements: 1.1, 2.2, 8.1, 13.1, 13.4_

  - [x] 4.3 Implement haunt creation with AI integration and preview

    - ✅ Create haunt creation endpoint that accepts URL and natural language description
    - ✅ Integrate AI configuration service into haunt creation flow
    - ✅ Add test scrape endpoint for setup wizard preview functionality
    - ✅ Add configuration preview endpoint for setup wizard
    - ✅ Add SSRF protection for all URL-accepting endpoints
    - ✅ Add error handling for AI service failures with fallback options
    - Write integration tests for AI-powered haunt creation
    - _Requirements: 1.1, 1.2, 10.1, 10.2, 10.3, 10.4, 16.1, 16.2, 16.3, 16.4, 16.5_

  - [x] 4.4 Add public haunt management endpoints
    - Implement make-public endpoint with public_slug generation
    - Create public haunt directory listing endpoint
    - Add public haunt detail endpoint accessible without authentication
    - Write tests for public haunt visibility and access controls
    - _Requirements: 8.2, 8.3, 8.4_

- [x] 5. Implement scraping service with Playwright

  - [x] 5.1 Create Playwright browser management

    - Implement browser pool management for concurrent scraping
    - Create page loading utilities with timeout and ready state handling
    - Add error handling for browser failures and page load issues
    - Write unit tests for browser management utilities
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 5.2 Build content extraction engine

    - Implement ScrapingService class with selector-based extraction
    - Create value normalization functions based on haunt configuration
    - Add support for CSS selectors and XPath expressions
    - Write unit tests for content extraction with mock HTML
    - _Requirements: 5.1, 5.2, 10.2, 10.3_

  - [x] 5.3 Implement change detection logic
    - Create state comparison functions for detecting key-value changes
    - Implement alert mode logic (once vs on_change) with state tracking
    - Add rate limiting for alerts per haunt
    - Write unit tests for change detection scenarios
    - _Requirements: 5.3, 6.1, 6.2, 6.3, 6.4_

- [x] 6. Set up Celery background processing

  - [x] 6.1 Configure Celery with Redis broker in Docker

    - Set up Celery configuration with Redis container as message broker
    - Configure periodic task scheduling for different scrape intervals
    - Add Celery worker and beat scheduler containers to docker-compose
    - Create Celery task base classes with error handling
    - _Requirements: 3.2, 3.3_

  - [x] 6.2 Implement scheduled scraping tasks

    - Create periodic Celery tasks for 15min, 30min, 60min, and daily intervals
    - Implement scrape_haunt task that processes individual haunts
    - Add task retry logic with exponential backoff for failures
    - Write integration tests for Celery task execution
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 6.3 Integrate scraping with change detection and alerts
    - Connect scraping tasks with change detection service
    - Implement alert sending logic within scraping tasks
    - Add RSS item creation when changes are detected
    - Write end-to-end tests for scraping workflow
    - _Requirements: 5.3, 6.1, 6.2, 6.3, 6.4, 7.1_

- [x] 7. Build RSS feed generation system

  - [x] 7.1 Create RSS XML generation service

    - Implement RSSService class with XML feed generation
    - Create RSS item formatting with title, description, link, and pubDate
    - Add support for AI-generated summaries in RSS descriptions
    - Write unit tests for RSS XML generation and validation
    - _Requirements: 7.1, 7.2, 7.4, 11.2, 11.3_

  - [x] 7.2 Implement RSS feed endpoints

    - Create private RSS feed endpoint with authentication
    - Implement public RSS feed endpoint using public_slug
    - Add RSS URL generation utility for haunt management
    - Write API tests for RSS feed accessibility and content
    - _Requirements: 7.3, 8.4_

  - [x] 7.3 Add RSS feed caching and optimization
    - Implement Redis caching for generated RSS feeds
    - Add cache invalidation when new RSS items are created
    - Optimize database queries for RSS item retrieval
    - Write performance tests for RSS feed generation
    - _Requirements: 7.3_

- [x] 8. Implement subscription management and UI preferences

  - [x] 8.1 Create subscription API endpoints

    - Implement subscription creation and deletion endpoints
    - Create user subscription listing with haunt details
    - Add subscription status checking utilities
    - Write API tests for subscription management
    - _Requirements: 9.1, 9.2_

  - [x] 8.2 Build enhanced read state tracking system

    - Implement UserReadState creation and updates with bulk operations
    - Create auto-mark-as-read API endpoints for scroll-based reading
    - Add star/unstar functionality with keyboard shortcut support
    - Create unread count aggregation for folders and haunts
    - Write unit tests for read state management
    - _Requirements: 9.3, 17.1, 17.2, 17.5, 17.6_

  - [x] 8.3 Create subscription-aware navigation API

    - Implement API endpoint for user's subscribed haunts in navigation format
    - Add unread count calculation for subscribed haunts and folders
    - Create subscription filtering and sorting options
    - Add UI preferences API for storing panel widths and settings
    - Write integration tests for subscription navigation
    - _Requirements: 9.1, 9.2, 9.3, 13.4_

  - [x] 8.4 Add immediate refresh and manual scraping endpoints
    - Create manual scrape trigger endpoint for individual haunts
    - Implement real-time status updates for ongoing scrape operations
    - Add rate limiting for manual refresh requests
    - Create WebSocket or polling mechanism for live updates
    - Write tests for manual refresh functionality
    - _Requirements: 17.7_

- [x] 9. Add AI summary generation

  - [x] 9.1 Implement change summary generation

    - Extend AIConfigService with summary generation method
    - Create change summary prompts and LLM integration
    - Add summary storage in RSS items and change records
    - Write unit tests for summary generation with mocked LLM responses
    - _Requirements: 11.1, 11.2, 11.3_

  - [x] 9.2 Integrate summaries into scraping workflow
    - Add optional summary generation to change detection process
    - Implement async summary generation to avoid blocking scraping
    - Add configuration option for enabling/disabling AI summaries per haunt
    - Write integration tests for summary generation in scraping workflow
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 10. Build web frontend interface

  - [x] 10.1 Create containerized React application with state management

    - Set up React application with Docker development container
    - Add frontend service to docker-compose with hot reload support
    - Implement Redux store with slices for haunts, items, and UI state
    - Create authentication components and protected routes
    - Add API client utilities for backend communication
    - _Requirements: All requirements need UI access_

  - [x] 10.2 Implement three-panel Google Reader layout

    - Create main layout component with resizable three-panel structure
    - Build navigation panel with folder tree and haunt list
    - Implement item list panel with change item cards
    - Create item detail panel with full change information
    - Add responsive design for mobile and tablet screens
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 10.3 Build folder organization interface

    - Create folder tree component with expand/collapse functionality
    - Implement drag-and-drop for organizing haunts into folders
    - Add unread count badges for folders and individual haunts
    - Create folder management (create, rename, delete) interface
    - Add context menus for folder and haunt operations
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 10.4 Implement item list and detail views

    - Create item card component with status change display
    - Add time-since-change formatting and visual indicators
    - Implement read/unread and starred item visual states
    - Build item detail view with change summary and metadata
    - Add "Visit Site" functionality and AI summary display
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 10.5 Create setup wizard interface

    - Build multi-step wizard modal for haunt creation
    - Implement URL input with validation and site preview
    - Create natural language description input with examples
    - Add folder selection, schedule, and privacy configuration
    - Implement test scrape preview with extracted data display
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [x] 10.6 Add Reader behaviors and keyboard shortcuts

    - Implement auto-mark-as-read when items are opened or scrolled past
    - Create keyboard navigation system (J/K for next/previous item)
    - Add keyboard shortcuts for mark read/unread (M) and star/unstar (S)
    - Implement refresh functionality for individual haunts
    - Create keyboard shortcuts help modal
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

  - [x] 10.7 Build subscription and public haunt interfaces
    - Create public haunt directory browsing interface
    - Implement subscription management for public haunts
    - Add subscription-aware navigation with read state tracking
    - Create user preference settings for UI customization
    - _Requirements: 7.1, 7.2, 9.1, 9.2, 9.3_

- [x] 11. Add comprehensive testing and error handling

  - [x] 11.1 Implement error handling and logging

    - Add comprehensive error handling for all service methods
    - Implement structured logging for debugging and monitoring
    - Create error response standardization across API endpoints
    - Add health check endpoints for system monitoring
    - _Requirements: All requirements need proper error handling_

  - [x] 11.2 Create comprehensive test suite

    - Write integration tests for complete user workflows
    - Add performance tests for concurrent scraping operations
    - Create end-to-end tests with real browser automation
    - Implement test data factories and fixtures
    - _Requirements: All requirements need test coverage_

  - [x] 11.3 Add monitoring and observability
    - Implement application metrics collection for scraping success rates
    - Add performance monitoring for database queries and API responses
    - Create alerting for system failures and performance degradation
    - Add resource usage monitoring for browser instances and workers
    - _Requirements: All requirements benefit from monitoring_
