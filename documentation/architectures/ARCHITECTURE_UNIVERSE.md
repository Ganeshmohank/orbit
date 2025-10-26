# Orbit Universe - Complete System Architecture

This document explains the entire Orbit system: how all components work together, where data flows, and how commands become actions.

---

## The Big Picture

Orbit is a multi-trigger productivity system with three main parts working together:

```
┌──────────────────────────────────────────────────────────────────┐
│                       ORBIT UNIVERSE                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRIGGER POINTS (Multiple Entry Points)                         │
│  ├─ Omi (voice commands)                                        │
│  ├─ Email (Zoom transcripts, notifications)                     │
│  ├─ API (Direct HTTP requests)                                  │
│  └─ And more...                                                 │
│                                                                  │
│  NEXUS (Middleware Brain)                                        │
│  ├─ Normalizes input from all sources                           │
│  ├─ Understands what you want                                   │
│  ├─ Routes commands to the right service                        │
│  └─ Maintains conversation context                              │
│                                                                  │
│  INTEGRATIONS                                                   │
│  ├─ Jira MCP (update tickets, create issues)                    │
│  ├─ Uber Service (book rides only)                              │
│  └─ Google Calendar MCP (schedule meetings/appointments only)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Multiple Trigger Points

Orbit doesn't just listen to Omi. It accepts commands from multiple sources:

### 1. Omi (Voice Commands)
- Wearable device that captures conversations
- Sends voice segments via webhook
- Includes GPS coordinates
- **See:** ARCHITECTURE_OMI.md for details

---

### 2. Email (Zoom Transcripts & Notifications)
- Receives meeting transcripts from Zoom
- Processes email notifications
- Extracts action items from transcripts
- Triggers automated tasks

**Example:**
```
Email from Zoom:
  Subject: Meeting Transcript - Sprint Planning
  Body: [Full meeting transcript]
  
Orbit:
  1. Receives email
  2. Extracts transcript
  3. Analyzes for action items
  4. Creates Jira tickets
  5. Sends Slack notification
```

---

### 3. API (Direct HTTP Requests)
- Direct webhook endpoint for external systems
- Structured JSON input
- Immediate processing
- Useful for integrations

**Example:**
```
POST /api/command
{
  "command": "update_ticket",
  "ticket_id": "PROJ-123",
  "status": "done"
}

Orbit:
  1. Receives API request
  2. Routes to Jira MCP
  3. Updates ticket
  4. Returns result
```

---

### 4. Future Trigger Points
- Slack messages
- Teams messages
- Calendar events
- Webhook from other services
- And more...

---

## How It Works: The Complete Flow

### Phase 1: Input Normalization

**What happens:**
- Command arrives from any trigger point (Omi, Email, API, etc.)
- Orbit normalizes the input to a standard format
- Extracts the core command and parameters

**Example:**

```
Omi input:
  segments: ["Book an Uber", "to Pier 39"]
  
Email input:
  transcript: "...we need to update ticket PROJ-123 to done..."
  
API input:
  command: "update_ticket"
  ticket_id: "PROJ-123"
  
All converted to:
  command_type: "update_ticket"
  parameters: {ticket_id: "PROJ-123", status: "done"}
```

---

### Phase 2: LLM Validation & Extraction

**What happens:**
- LLM (OpenAI) analyzes the normalized command
- Determines command type
- Extracts parameters and context
- Validates it's a real request

**Example:**
```
Input: "Book an Uber to Pier 39"
Output: 
  - command_type: "ride_booking"
  - destination: "Pier 39"
  - confidence: 0.95

Input: "Update ticket PROJ-123 to done"
Output:
  - command_type: "jira_update"
  - ticket_id: "PROJ-123"
  - status: "done"
  - confidence: 0.98
```

**LLM Rules:**
- ✅ Accepts real location names and ticket IDs
- ✅ Corrects spelling and typos
- ❌ Rejects generic or ambiguous terms

---

### Phase 3: Context Enrichment

**What happens:**
- System adds context from conversation history
- Retrieves user preferences
- Gets location data if needed
- Loads authentication status

**Example:**
```
Command: "Book an Uber"
Context added:
  - User location: Ferry Building (from GPS)
  - Destination: Pier 39 (from previous context)
  - User authenticated: true
  - Preferred ride type: UberX
```

---

### Phase 4: Service Routing

**What happens:**
- Nexus determines which MCP server to use
- Routes command to appropriate service
- Passes all necessary parameters

**Example:**
```
Command: "Book an Uber to Pier 39"
└─ Route to: Uber Service
└─ Pass: pickup="Ferry Building", destination="Pier 39"

Command: "Update ticket PROJ-123 to done"
└─ Route to: Jira MCP
└─ Pass: ticket_id="PROJ-123", status="done"

Command: "Schedule a meeting tomorrow at 2pm"
└─ Route to: Google Calendar MCP
└─ Pass: title="meeting", date="tomorrow", time="14:00"
```

---

### Phase 5: Authentication & Validation

**What happens:**
- System checks if user has permission
- Loads saved credentials if needed
- Validates session is still active
- Checks rate limits

**If validation fails:**
- Request is rejected
- User is notified
- Error is logged

---

### Phase 6: Execute Action

**What happens:**
- MCP server connects to external service
- Performs the requested action
- Captures result and any errors
- Returns structured response

**Example:**
```
Uber Service (Book Ride):
  1. Load saved session
  2. Open Uber website
  3. Fill pickup and destination
  4. Select ride type
  5. Click "Request"
  6. Return: driver, ETA, vehicle

Jira MCP (Update Ticket):
  1. Connect to Jira API
  2. Find ticket PROJ-123
  3. Update status to "Done"
  4. Return: success, timestamp

Google Calendar MCP (Schedule Meeting):
  1. Connect to Google Calendar API
  2. Create event with date/time
  3. Add to user's calendar
  4. Return: event_id, confirmation
```

---

### Phase 7: Result Processing & Notification

**What happens:**
- Result is processed and formatted
- Confirmation is sent back to trigger source
- Notifications sent to relevant services
- Action is logged

**Example:**
```
Omi trigger:
  └─ Send confirmation back to Omi device
  └─ User hears: "Your Uber is booked"

Email trigger:
  └─ Send confirmation email
  └─ Include action items created

API trigger:
  └─ Return JSON response
  └─ Include result details
```

---

## Communication Points

### 1. Trigger Points → Nexus

**Omi Webhook:**
```
POST /webhook
{
  "segments": [{"text": "Book an Uber to Pier 39", "speaker": "user"}],
  "gps_lat": 37.7749,
  "gps_lon": -122.4194
}
```
**See:** ARCHITECTURE_OMI.md for details

---

**Email Webhook:**
```
POST /email
{
  "from": "zoom@zoom.us",
  "subject": "Meeting Transcript - Sprint Planning",
  "body": "[Full meeting transcript]"
}
```

---

**API Endpoint:**
```
POST /api/command
{
  "command": "update_ticket",
  "ticket_id": "PROJ-123",
  "status": "done",
  "user_id": "user123"
}
```

---

### 2. Nexus → LLM (OpenAI)

**What Nexus sends:**
- Normalized command text
- Context from conversation history
- User preferences
- Any extracted parameters

**What LLM returns:**
- Command type classification
- Extracted parameters
- Confidence score
- Suggested actions

---

### 3. Nexus → Services

**For Jira:**
```
Command: "Update ticket PROJ-123 to done"
Nexus → Jira MCP → Jira REST API → Update ticket
```

**For Google Calendar:**
```
Command: "Schedule meeting tomorrow at 2pm"
Nexus → Google Calendar MCP → Google Calendar API → Create event
```

**For Uber:**
```
Command: "Book an Uber to Pier 39"
Nexus → Uber Service → Browser Automation → Uber website
```

---

### 4. Services → External APIs

Each service connects to its respective platform:
- **Jira MCP** → Jira REST API (authenticated with API token)
- **Google Calendar MCP** → Google Calendar API (authenticated with OAuth)
- **Uber Service** → Browser automation (uses saved session cookies)

---

## Data Storage

### User Data
**Location:** `users/{uid}.json`

**Contains:**
- Authentication status
- Last booking details
- User preferences

---

### Session Data
**Location:** `sessions/{uid}_uber_session.json`

**Contains:**
- Cookies (for Uber authentication)
- localStorage data
- Session state

---

### Screenshots
**Location:** `snapshots/{uid}/`

**Contains:**
- Step-by-step booking process images
- Useful for debugging and verification

---

## Authentication & Authorization

### Service Authentication

Each MCP server manages its own authentication:

**Jira:**
- API token stored in environment variables
- Validated on each request
- Domain URL configured in environment

**Google Calendar:**
- OAuth tokens for user calendars
- Refresh tokens managed automatically
- Scopes: calendar.events, calendar.readonly

**Uber:**
- Session cookies stored locally in `sessions/{uid}_uber_session.json`
- 2FA handled during initial setup
- Session validated before each booking

---

### User Authorization

Before executing any command:
1. Verify user identity
2. Check service permissions
3. Validate rate limits
4. Load user preferences

---

## Rate Limiting

**Purpose:** Prevent abuse and accidental duplicate actions

**Rules:**
- Minimum 30 seconds between similar commands per user
- Maximum 10 commands per minute per user
- Service-specific limits (Jira, Slack, etc.)

**Example:**
```
t=0s: Update ticket ✅
t=10s: Try update again ❌ (too soon)
t=35s: Update different ticket ✅ (30 seconds passed)
```

---

## Error Handling

### Validation Errors

**"Command not recognized"**
- LLM couldn't determine command type
- Solution: Rephrase with specific details

**"Missing required parameters"**
- Command incomplete (e.g., no destination)
- Solution: Provide all required information

---

### Authentication Errors

**"User not authenticated"**
- Service credentials missing or expired
- Solution: Re-authenticate via service setup

**"Permission denied"**
- User lacks permission for action
- Solution: Check service permissions

---

### Service Errors

**"Service unavailable"**
- External service is down
- Solution: Retry later

**"Invalid parameters"**
- Parameters don't match service requirements
- Solution: Verify parameters and retry

---

### Rate Limit Errors

**"Rate limited"**
- Too many commands in short time
- Solution: Wait before next command

---

## Extensibility: Adding New Services

### Current Services
- **Jira** - Ticket management
- **Google Calendar** - Meeting scheduling
- **Uber** - Ride booking

### To add a new service (e.g., Slack):

1. **Create MCP Server** for Slack
   - File: `middleware/mcp_slack.py`
   - Handles Slack API calls
   - Manages authentication

2. **Update Nexus** (`middleware/agent.py`)
   - Add Slack routing logic in command router
   - Handle Slack-specific commands

3. **Update Command Detector** (`ride_detector.py`)
   - Recognize Slack commands
   - Extract message content

4. **Add Environment Variables** (`.env`)
   - SLACK_BOT_TOKEN
   - SLACK_WORKSPACE_ID

5. **Test**
   - "Send a message to #general: Project is done"
   - System routes to Slack MCP
   - Message sent

---

## System Components

### Main FastAPI App (`main.py`)
- Receives webhook requests
- Manages authentication flow
- Coordinates booking process
- Serves web UI

### Nexus Agent (`middleware/agent.py`)
- Analyzes meeting transcripts (for action items)
- Extracts action items from conversations
- Routes commands to appropriate services
- Maintains conversation context
- Supports: Jira MCP (tickets), Google Calendar MCP (meetings), Uber Service (rides)

### Command Detector (`ride_detector.py`)
- LLM-powered command validation
- Location extraction (for Uber ride booking)
- Geolocation handling (GPS + IP fallback)
- Spell correction

### Browser Automation (`uber_automation.py`)
- Opens Uber website
- Fills in pickup and destination for ride booking
- Selects ride type
- Captures screenshots of booking process
- Handles edge cases and errors

### Storage (`simple_storage.py`)
- Saves user data to `users/{uid}.json`
- Manages session files in `sessions/`
- Handles file I/O operations

### Authentication (`auth_manager.py`)
- Handles Uber login flow
- Detects 2FA requirements
- Saves authenticated sessions
- Validates session status

---

## Environment Variables

**Required:**
```
OPENAI_API_KEY          - For LLM command processing
GOOGLE_API_KEY          - For Google Calendar integration
JIRA_API_TOKEN          - For Jira ticket management
JIRA_DOMAIN             - Jira instance domain (e.g., company.atlassian.net)
```

**Optional:**
```
PORT                    - Server port (default: 8000)
AUTO_REQUEST            - Auto-book Uber rides (default: false)
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Home page with status |
| `/health` | GET | Health check |
| `/auth` | GET | Start authentication |
| `/auth-status` | GET | Check auth status |
| `/submit-2fa-code` | POST | Submit 2FA code |
| `/setup-completed` | GET | Check if authenticated |
| `/webhook` | POST | Receive voice commands |

---

## Key Features

### ✅ Voice Command Processing
- Sliding window segment collection
- LLM-powered validation
- Natural language understanding

### ✅ Smart Location Detection
- GPS-based pickup location
- IP geolocation fallback
- Landmark reverse geocoding

### ✅ Secure Authentication
- One-time login setup
- 2FA support
- Session persistence

### ✅ Extensible Architecture
- MCP protocol for service integration
- Easy to add new services
- Modular design

### ✅ Comprehensive Logging
- Detailed operation tracking
- Error diagnostics
- Debugging information

---

## Deployment

### Docker
```bash
docker-compose up
```

### Railway
```bash
railway link
railway variables set OPENAI_API_KEY=your_key
railway up
```

### Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Summary

Orbit is a unified system where:

1. **Omi** listens and captures your voice
2. **Nexus** understands what you want
3. **MCP Servers** execute the action
4. **Result** comes back to you

All components communicate through simple, well-defined interfaces. The system is designed to be extended with new services without modifying core logic.

---

**Built with ❤️ for voice-activated productivity**
