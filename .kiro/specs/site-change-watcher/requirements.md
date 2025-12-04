# Requirements Document

## Introduction

The Site Change Watcher feature resurrects the Google Reader experience for the modern web by "haunting" live sites (including SPAs) to detect user-defined changes and exposing those changes via RSS feeds and a Reader-style UI. Users can define targets using natural language, and the system automatically monitors these sites for changes, generating RSS feeds and providing a familiar reader interface.

## Requirements

### Requirement 1

**User Story:** As a user, I want to define new haunts using natural language descriptions, so that I can easily set up monitoring without technical knowledge.

#### Acceptance Criteria

1. WHEN a user provides a URL and natural language description THEN the system SHALL accept both inputs for haunt creation
2. WHEN the system receives a natural language description THEN it SHALL use an LLM to convert the description into structured configuration
3. WHEN the LLM processes the description THEN it SHALL generate CSS/XPath selectors for data extraction
4. WHEN the LLM processes the description THEN it SHALL create normalization rules for the tracked values
5. WHEN the LLM processes the description THEN it SHALL define "truthy" values for change detection

### Requirement 2

**User Story:** As a user, I want my haunt configurations to be stored and editable, so that I can modify monitoring parameters after creation.

#### Acceptance Criteria

1. WHEN a haunt configuration is generated THEN the system SHALL store it as structured JSON
2. WHEN a user requests to edit a haunt THEN the system SHALL display the current configuration in an editable format
3. WHEN a user modifies a haunt configuration THEN the system SHALL validate and save the changes
4. WHEN a haunt configuration is stored THEN it SHALL include selectors, normalization rules, and truthy value mappings

### Requirement 3

**User Story:** As a user, I want to set custom scraping intervals for each haunt, so that I can control monitoring frequency based on my needs.

#### Acceptance Criteria

1. WHEN creating a haunt THEN the user SHALL be able to specify a scraping interval (15, 30, 60 minutes, or daily)
2. WHEN a scraping interval is set THEN the system SHALL schedule periodic scrape jobs automatically
3. WHEN the system schedules scrape jobs THEN it SHALL use Celery periodic tasks for execution
4. WHEN a haunt is updated THEN the system SHALL reschedule the scrape jobs with the new interval

### Requirement 4

**User Story:** As a system, I want to scrape SPA content effectively, so that I can monitor modern web applications that rely heavily on JavaScript.

#### Acceptance Criteria

1. WHEN scraping a URL THEN the system SHALL use Playwright headless browser for rendering
2. WHEN loading a page THEN the system SHALL wait for DOM ready state before extraction
3. WHEN loading JavaScript-heavy pages THEN the system SHALL implement appropriate timeouts
4. WHEN a page fails to load within timeout THEN the system SHALL log the failure and continue with next scheduled scrape

### Requirement 5

**User Story:** As a system, I want to track only key-value state changes, so that I can efficiently detect changes without storing large amounts of data.

#### Acceptance Criteria

1. WHEN scraping completes THEN the system SHALL extract only the configured keys from the page
2. WHEN values are extracted THEN the system SHALL normalize them according to the stored configuration
3. WHEN normalized values are obtained THEN the system SHALL compare them with the last known state
4. WHEN storing state THEN the system SHALL NOT persist full HTML or large text blocks
5. WHEN storing state THEN the system SHALL only save key/value pairs and minimal diff information

### Requirement 6

**User Story:** As a user, I want to receive alerts when changes occur, so that I can be notified of important updates based on my preferences.

#### Acceptance Criteria

1. WHEN a state change is detected AND alert_mode is "once" AND no previous alert was sent THEN the system SHALL send an alert and store last_alert_state
2. WHEN a state change is detected AND alert_mode is "on_change" THEN the system SHALL send an alert for any tracked key difference
3. WHEN alerts are sent THEN the system SHALL optionally rate-limit alerts per haunt (max 1 per N minutes)
4. WHEN an alert is sent THEN the system SHALL update the haunt's alert tracking state

### Requirement 7

**User Story:** As a user, I want RSS feeds generated from my haunts, so that I can subscribe to changes using standard RSS readers.

#### Acceptance Criteria

1. WHEN a haunt experiences state changes THEN the system SHALL maintain an RSS feed representation
2. WHEN creating RSS items THEN each item SHALL contain a descriptive title, the haunted URL as link, change summary as description, and timestamp
3. WHEN generating RSS feeds THEN the system SHALL build them either on-the-fly from database state or from materialized RSS item tables
4. WHEN AI summaries are available THEN the system SHALL optionally include them in RSS item descriptions

### Requirement 8

**User Story:** As a user, I want to control the privacy of my haunts, so that I can keep some private and share others publicly.

#### Acceptance Criteria

1. WHEN creating a haunt THEN it SHALL be private to the owner by default
2. WHEN a user marks a haunt as public THEN the system SHALL generate a stable public_slug
3. WHEN a haunt is public THEN it SHALL appear in a public directory
4. WHEN a haunt is public THEN it SHALL expose RSS URLs accessible to any user or anonymous client

### Requirement 9

**User Story:** As a user, I want to subscribe to public haunts created by others, so that I can benefit from monitoring setups shared by the community.

#### Acceptance Criteria

1. WHEN a user subscribes to a public haunt THEN it SHALL appear in their left-hand navigation
2. WHEN viewing subscribed haunts THEN users SHALL be able to star items for later reference
3. WHEN viewing subscribed haunts THEN users SHALL be able to track read/unread state locally
4. WHEN browsing public haunts THEN users SHALL see a directory of available public haunts

### Requirement 10

**User Story:** As a system, I want to use AI for configuration derivation, so that users can set up monitoring using natural language.

#### Acceptance Criteria

1. WHEN a haunt is created THEN the system SHALL call the LLM once to derive configuration
2. WHEN the LLM processes the natural language description THEN it SHALL generate appropriate CSS/XPath selectors
3. WHEN the LLM processes the description THEN it SHALL create normalization rules for extracted values
4. WHEN the LLM processes the description THEN it SHALL identify values to treat as "open/closed/interesting"

### Requirement 11

**User Story:** As a user, I want AI-generated summaries of changes, so that I can quickly understand what changed without examining raw data.

#### Acceptance Criteria

1. WHEN a change occurs THEN the system SHALL optionally call the LLM to generate a human-friendly summary
2. WHEN generating summaries THEN the LLM SHALL create a 1-sentence description of the change
3. WHEN a summary is generated THEN it SHALL be stored in the minimal diff and RSS item
4. WHEN AI analysis is performed THEN it SHALL only occur at haunt creation and optionally at change detection time

### Requirement 12

**User Story:** As a user, I want a Google Reader-style three-panel layout, so that I can efficiently navigate and read change items.

#### Acceptance Criteria

1. WHEN accessing the main interface THEN the system SHALL display a three-panel layout
2. WHEN displaying the left panel THEN it SHALL show navigation with folders and haunts
3. WHEN displaying the middle panel THEN it SHALL show a list of change items for the selected haunt
4. WHEN displaying the right panel THEN it SHALL show full item detail with summary and metadata
5. WHEN no haunt is selected THEN the middle and right panels SHALL show appropriate empty states

### Requirement 13

**User Story:** As a user, I want to organize my haunts into folders, so that I can group related monitoring targets.

#### Acceptance Criteria

1. WHEN creating or editing a haunt THEN the user SHALL be able to assign it to a folder
2. WHEN viewing navigation THEN haunts SHALL be grouped by their assigned folders
3. WHEN a folder contains haunts THEN it SHALL display an aggregate unread count badge
4. WHEN a haunt has unread items THEN it SHALL display an individual unread count badge
5. WHEN folders are displayed THEN they SHALL be collapsible and expandable

### Requirement 14

**User Story:** As a user, I want to see change items in a scannable list format, so that I can quickly identify important updates.

#### Acceptance Criteria

1. WHEN displaying change items THEN each item SHALL show a short status line indicating the change
2. WHEN displaying change items THEN each item SHALL show the time since the change occurred
3. WHEN displaying change items THEN each item SHALL show icons for unread and starred status
4. WHEN displaying status changes THEN the format SHALL be "Status: OLD_VALUE → NEW_VALUE"
5. WHEN items are unread THEN they SHALL be visually distinguished from read items

### Requirement 15

**User Story:** As a user, I want detailed item views, so that I can see complete information about changes.

#### Acceptance Criteria

1. WHEN an item is selected THEN the detail view SHALL show the change summary
2. WHEN an item is selected THEN the detail view SHALL show a link to visit the original site
3. WHEN an AI summary is available THEN the detail view SHALL display it prominently
4. WHEN an item has a change history THEN the detail view SHALL optionally show a timeline of prior changes
5. WHEN displaying item details THEN all metadata SHALL be clearly presented

### Requirement 16

**User Story:** As a user, I want a guided setup process for creating haunts, so that I can easily configure monitoring targets.

#### Acceptance Criteria

1. WHEN creating a new haunt THEN the system SHALL provide a dedicated setup wizard
2. WHEN using the setup wizard THEN the user SHALL be able to enter a URL and natural language description
3. WHEN using the setup wizard THEN the user SHALL be able to choose folder, schedule, alert mode, and privacy settings
4. WHEN using the setup wizard THEN the system SHALL provide a preview by running a test scrape
5. WHEN showing the preview THEN the system SHALL display extracted keys and values for user verification

### Requirement 17

**User Story:** As a user, I want Reader-style behaviors and keyboard shortcuts, so that I can efficiently manage large numbers of change items.

#### Acceptance Criteria

1. WHEN an item is opened in the detail view THEN it SHALL be automatically marked as read
2. WHEN an item is scrolled past in the list THEN it SHALL optionally be marked as read
3. WHEN the user presses 'J' THEN the selection SHALL move to the next item
4. WHEN the user presses 'K' THEN the selection SHALL move to the previous item
5. WHEN the user presses 'M' THEN the current item SHALL toggle between read and unread
6. WHEN the user presses 'S' THEN the current item SHALL toggle between starred and unstarred
7. WHEN viewing a haunt THEN there SHALL be a refresh button to trigger immediate scraping