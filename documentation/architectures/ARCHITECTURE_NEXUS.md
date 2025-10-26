# Nexus - Middleware Brain

Nexus is the intelligent middleware that understands commands and routes them to the right services.

---

## What Nexus Does

Nexus is the brain of Orbit:
- Receives voice segments from Omi
- Understands what you want (using LLM)
- Routes commands to appropriate services
- Maintains conversation context
- Returns results back to Omi

---

## Nexus's Role in Orbit

```
┌──────────────────────────────────────────────────────────────┐
│  Commands from any trigger point                             │
│  (Omi, Email, API)                                           │
└──────────────┬───────────────────────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────┐
│  NEXUS MIDDLEWARE                                            │
│                                                              │
│  1. Normalize input                                          │
│  2. Validate with LLM                                        │
│  3. Extract command details                                  │
│  4. Route to service                                         │
│  5. Execute action                                           │
│  6. Return result                                            │
└──────────────┬───────────────────────────────────────────────┘
               │
               ├─────────────┬──────────────┬──────────────┐
               ↓             ↓              ↓
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │  Uber   │  │  Jira    │  │ Google   │
         │ Service │  │  MCP     │  │ Calendar │
         │          │  │          │  │  MCP     │
         └──────────┘  └──────────┘  └──────────┘
```

---

## How Nexus Works

### Phase 1: Normalize Input

**What happens:**
- Command arrives from any trigger point (Omi, Email, API)
- Nexus normalizes the input to standard format
- Extracts core command and parameters

**For Omi (voice segments):**
- Collects segments for 5 seconds of silence (sliding window)
- Combines segments into single text
- Passes to LLM

**For Email:**
- Extracts transcript or content
- Identifies action items
- Passes to LLM

**For API:**
- Validates JSON structure
- Extracts command and parameters
- Passes to LLM

---

### Phase 2: Validate with LLM

**What happens:**
- Combine all segments into one text
- Send to OpenAI for analysis
- LLM determines command type

**Example:**
```
Input segments:
  1. "Book an Uber"
  2. "to Pier 39"

Combined: "Book an Uber to Pier 39"

LLM Analysis:
  - Command type: ride_booking
  - Start location: null
  - End location: "Pier 39"
  - Confidence: 0.95
```

**LLM Rules:**
- ✅ Accept real locations (Pier 39, SJSU, Airport)
- ✅ Correct spelling (Pear 39 → Pier 39)
- ❌ Reject generic terms (My office, Home, Work)

---

### Phase 3: Extract Command Details

**For Ride Booking:**
```
Input: "Book an Uber from SJSU to downtown"
Output:
  - start_location: "SJSU"
  - end_location: "downtown"
  - ride_type: null (not specified)
```

**For Jira (Future):**
```
Input: "Update ticket PROJ-123 to done"
Output:
  - ticket_id: "PROJ-123"
  - action: "update"
  - status: "done"
```

**For Calendar (Future):**
```
Input: "Schedule a meeting tomorrow at 2pm"
Output:
  - event_title: "meeting"
  - date: "tomorrow"
  - time: "14:00"
```

---

### Phase 4: Determine Pickup Location

**If only destination provided:**

```
You say: "Book an Uber to Pier 39"
Nexus needs: Where are you?

Priority:
  1. GPS from device (if provided)
  2. IP geolocation (fallback)
  3. Hardcoded landmark (last resort)

Example with GPS:
  GPS: (37.7749, -122.4194)
  └─ Find nearest landmark
  └─ Result: "Ferry Building"
  └─ Final route: Ferry Building → Pier 39
```

---

### Phase 5: Validate Authentication

**Check user session:**
```
1. Load saved session from disk
2. Verify cookies are valid
3. Check if session is expired
4. If valid: proceed to booking
5. If invalid: prompt re-authentication
```

---

### Phase 6: Route to Service

**Nexus decides which service to use:**

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

### Phase 7: Execute Action

**For Uber (Book Ride):**
- Open browser with saved session
- Fill pickup location
- Fill destination location
- Select ride type
- Click "Request"
- Capture screenshots

**For Jira (Update Ticket):**
- Connect to Jira REST API
- Find ticket by ID
- Update ticket status
- Add comment if needed
- Return confirmation

**For Google Calendar (Schedule Meeting):**
- Connect to Google Calendar API
- Create event with date/time
- Add to user's calendar
- Return confirmation

---

### Phase 8: Return Result

**Response to Omi:**
```json
{
  "success": true,
  "message": "Uber booked successfully",
  "details": {
    "driver": "John",
    "eta": "5 minutes",
    "vehicle": "Toyota Prius"
  }
}
```

---

## Nexus Components

### 1. Webhook Handler (`main.py`)
- Receives voice segments
- Manages sliding window
- Coordinates processing

### 2. LLM Validator (`ride_detector.py`)
- Validates command type
- Extracts locations
- Corrects spelling

### 3. Geolocation Handler (`ride_detector.py`)
- Gets GPS coordinates
- Performs IP geolocation
- Finds nearest landmark

### 4. Authentication Manager (`auth_manager.py`)
- Loads saved sessions
- Validates cookies
- Handles 2FA

### 5. Service Routers (`middleware/agent.py`)
- Routes to Uber MCP
- Routes to Jira MCP
- Routes to Calendar MCP
- Routes to Slack MCP

### 6. Execution Engines
- Browser automation (Uber)
- API clients (Jira, Slack, Calendar)

---

## Command Processing Pipeline

```
Voice Segments
      ↓
Collect (5 sec window)
      ↓
Combine Text
      ↓
LLM Validation
      ├─ Is this a valid command?
      ├─ What type of command?
      └─ Extract parameters
      ↓
Determine Service
      ├─ Ride booking → Uber MCP
      ├─ Ticket update → Jira MCP
      ├─ Meeting → Calendar MCP
      └─ Message → Slack MCP
      ↓
Validate Authentication
      ├─ User authenticated?
      ├─ Session valid?
      └─ Permissions granted?
      ↓
Execute Action
      ├─ Connect to service
      ├─ Perform operation
      └─ Capture result
      ↓
Return Result
      └─ Send back to Omi
```

---

## Rate Limiting

**Purpose:** Prevent accidental double-bookings

**Implementation:**
```
Minimum 30 seconds between bookings per user

Example:
  t=0s: Book ride 1 ✅
  t=10s: Try book ride 2 ❌ (too soon)
  t=35s: Book ride 2 ✅ (30 seconds passed)
```

---

## Error Handling

### Validation Errors

**LLM rejects command:**
```
Input: "Book an Uber to my office"
LLM: "Generic term detected"
Result: Command rejected
Action: Log and skip
```

**Missing required parameters:**
```
Input: "Book an Uber"
LLM: "Destination not specified"
Result: Command rejected
Action: Log and skip
```

### Authentication Errors

**Session expired:**
```
Result: "Session expired"
Action: Prompt user to re-authenticate
```

**User not authenticated:**
```
Result: "User not authenticated"
Action: Redirect to /auth endpoint
```

### Service Errors

**Uber booking failed:**
```
Result: "Could not find pickup location"
Action: Log error and notify user
```

**Jira API error:**
```
Result: "Ticket not found"
Action: Log error and notify user
```

---

## Conversation Context

**Nexus remembers:**
- Previous commands in session
- User preferences
- Service states

**Example:**
```
User: "Book an Uber to Pier 39"
Nexus: Books ride

User: "Cancel it"
Nexus: Understands "it" = the Uber ride
Nexus: Cancels the ride
```

---

## Extensibility

### Adding a New Service

**Step 1: Create MCP Server**
```
middleware/mcp_slack.py
- Handle Slack API
- Manage authentication
```

**Step 2: Update Nexus Router**
```
middleware/agent.py
- Add Slack routing logic
- Handle Slack responses
```

**Step 3: Update Command Detector**
```
ride_detector.py
- Recognize Slack commands
- Extract message content
```

**Step 4: Add Environment Variables**
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C123...
```

**Step 5: Test**
```
"Send a message to #general: Project is done"
Nexus routes to Slack MCP
Message sent ✅
```

---

## Configuration

### Environment Variables

```
OPENAI_API_KEY          - For LLM processing
GOOGLE_API_KEY          - For meeting analysis
JIRA_API_TOKEN          - For Jira integration
JIRA_DOMAIN             - Jira instance domain
SLACK_BOT_TOKEN         - For Slack integration
CALENDAR_API_KEY        - For calendar integration
PORT                    - Server port (default: 8000)
AUTO_REQUEST            - Auto-book rides (default: false)
```

---

## Logging

Nexus logs every step for debugging:

```
📥 Webhook received for uid=default_user
📊 Payload: 2 segment(s)
  Segment 1: speaker='user', text='Book an Uber'
  Segment 2: speaker='user', text='to Pier 39'
⏱️ Last segment at 1729950000, waiting 5s from now...
✅ 5 seconds of silence detected
✅ Joined text: 'Book an Uber to Pier 39'
✅ LLM validation passed: SJSU → Pier 39
📍 Using GPS coordinates: (37.7749, -122.4194)
🏛️ Nearest landmark: Ferry Building
✅ Got pickup location: Ferry Building
🎯 Final booking route: Ferry Building → Pier 39
🔒 Booking marked as ACTIVE
🚗 Starting booking: Ferry Building → Pier 39
✅ Booking successful
📊 Driver: John, ETA: 5 minutes
```

---

## Performance

### Processing Time

```
Segment collection:    5 seconds (sliding window)
LLM validation:        1-2 seconds
Location extraction:   <1 second
Authentication check:  <1 second
Booking execution:     10-30 seconds
Total:                 ~20-40 seconds
```

### Concurrency

- Handles multiple users simultaneously
- Each user has separate bucket
- Independent processing pipelines

---

## Summary

Nexus is the intelligent middleware that:
- Collects and validates voice commands
- Understands natural language
- Routes to appropriate services
- Executes actions
- Returns results

It's the bridge between Omi (voice input) and MCP Servers (service execution).

---

**Built with ❤️ for voice-activated productivity**
