# MCP Servers - Service Integrations

MCP Servers are the execution engines that connect Orbit to external services via APIs.

---

## What MCP Servers Do

MCP (Model Context Protocol) Servers are specialized connectors that:
- Connect to external services (Jira, Google Calendar)
- Execute commands on those services via REST APIs
- Return results to Nexus
- Handle authentication with each service

Note: Uber is a direct service integration (not MCP) using browser automation.

---

## MCP in Orbit

```
┌──────────────────────────────────────────────────────────────┐
│  NEXUS (Middleware)                                          │
│  - Receives command from any trigger point                   │
│  - Validates and extracts parameters                         │
│  - Routes to appropriate service                             │
└──────────────┬───────────────────────────────────────────────┘
               │
               ├──────────────┬──────────────┬──────────────┐
               ↓              ↓              ↓
        ┌────────────┐ ┌────────────┐ ┌────────────┐
        │ Uber       │ │ Jira MCP   │ │ Google Cal │
        │ Service    │ │            │ │ MCP        │
        │            │ │ - Update   │ │ - Create   │
        │ - Book     │ │   tickets  │ │   events   │
        │   ride     │ │ - Create   │ │ - Schedule │
        │            │ │   issues   │ │   meetings │
        │            │ │ - Assign   │ │            │
        │            │ │   tasks    │ │            │
        └────────────┘ └────────────┘ └────────────┘
               │              │              │
               ↓              ↓              ↓
        ┌────────────┐ ┌────────────┐ ┌────────────┐
        │   Uber     │ │   Jira     │ │  Google    │
        │ Automation │ │   API      │ │  Calendar  │
        │            │ │            │ │   API      │
        └────────────┘ └────────────┘ └────────────┘
```

---

## Available Services

Currently implemented: **2 MCP Servers + 1 Direct Service**

### 1. Uber Service (Not MCP)

**Purpose:** Book Uber rides only

**Commands:**
```
"Book an Uber to Pier 39"
"Get me a ride from SJSU to downtown"
```

**Operations:**
- Book ride with pickup and destination
- Select ride type (UberX, UberXL, etc.)
- Capture booking confirmation

**Authentication:**
- Uses saved Uber session (cookies)
- Requires one-time login via `/auth`

**Example Flow:**
```
Command: "Book an Uber to Pier 39"
         ↓
Nexus extracts: pickup="Ferry Building", destination="Pier 39"
         ↓
Uber MCP receives parameters
         ↓
Opens Uber website with saved session
         ↓
Fills pickup and destination
         ↓
Selects ride type
         ↓
Clicks "Request"
         ↓
Captures screenshots
         ↓
Returns: driver="John", eta="5 minutes"
```

---

### 2. Jira MCP

**Purpose:** Manage Jira tickets and issues

**Commands:**
```
"Update ticket PROJ-123 to done"
"Create a new bug ticket"
"Show me my assigned tickets"
"Assign PROJ-456 to John"
```

**Operations:**
- Update ticket status
- Create new issues
- Add comments
- Assign tickets
- Get ticket details
- List assigned tickets

**Authentication:**
- Jira API token (from environment)
- Jira domain (from environment)

**Example Flow:**
```
Command: "Update ticket PROJ-123 to done"
         ↓
Nexus extracts: ticket_id="PROJ-123", status="done"
         ↓
Jira MCP receives parameters
         ↓
Connects to Jira API
         ↓
Updates ticket status
         ↓
Returns: success=true, message="Ticket updated"
```

---

### 3. Google Calendar MCP

**Purpose:** Schedule meetings and create appointments only

**Commands:**
```
"Schedule a meeting tomorrow at 2pm"
"Create an appointment with the team at 3pm"
"Add a meeting next Monday at 10am"
```

**Operations:**
- Create calendar events
- Schedule meetings with time and date
- Create appointments
- Set meeting duration

**Authentication:**
- Google Calendar API key (from environment)
- OAuth for user calendar access

**Example Flow:**
```
Command: "Schedule a meeting tomorrow at 2pm"
         ↓
Nexus extracts: title="meeting", date="tomorrow", time="14:00"
         ↓
Google Calendar MCP receives parameters
         ↓
Connects to Google Calendar API
         ↓
Creates event on calendar
         ↓
Returns: event_id="abc123", confirmation="Meeting scheduled"
```

---

## MCP Server Structure

### Basic Template

```python
class ServiceMCP:
    def __init__(self, api_key, domain=None):
        """Initialize MCP with credentials"""
        self.api_key = api_key
        self.domain = domain
    
    async def authenticate(self):
        """Verify credentials are valid"""
        pass
    
    async def execute_command(self, command, parameters):
        """Execute the command"""
        pass
    
    async def get_status(self):
        """Get service status"""
        pass
```

### Example: Uber MCP

```python
class UberMCP:
    def __init__(self, session_path):
        self.session_path = session_path
    
    async def book_ride(self, pickup, destination):
        """Book an Uber ride"""
        # Load session
        # Open browser
        # Fill locations
        # Click request
        # Return result
        pass
    
    async def cancel_ride(self, ride_id):
        """Cancel active ride"""
        pass
    
    async def get_eta(self, ride_id):
        """Get driver ETA"""
        pass
```

---

## Communication Protocol

### Nexus → MCP Server

**Request Format:**
```json
{
  "command": "book_ride",
  "parameters": {
    "pickup": "Ferry Building",
    "destination": "Pier 39",
    "ride_type": "UberX"
  }
}
```

**Fields:**
- `command` - What to do (book_ride, update_ticket, etc.)
- `parameters` - Command-specific parameters

---

### MCP Server → Nexus

**Response Format:**
```json
{
  "success": true,
  "message": "Ride booked successfully",
  "data": {
    "driver": "John",
    "eta": "5 minutes",
    "vehicle": "Toyota Prius",
    "license_plate": "ABC123"
  }
}
```

**Fields:**
- `success` - Whether command succeeded
- `message` - Human-readable message
- `data` - Command-specific result data

---

## Error Handling

### Service Unavailable

```json
{
  "success": false,
  "error": "service_unavailable",
  "message": "Uber API is currently unavailable"
}
```

### Authentication Failed

```json
{
  "success": false,
  "error": "auth_failed",
  "message": "Invalid API credentials"
}
```

### Invalid Parameters

```json
{
  "success": false,
  "error": "invalid_parameters",
  "message": "Destination location not found"
}
```

---

## Adding a New MCP Server

### Current Services
- **Uber** - Ride booking (browser automation)
- **Jira** - Ticket management (REST API)
- **Google Calendar** - Meeting scheduling (REST API)

### To add a new service (e.g., Slack):

### Step 1: Create MCP Class

**File:** `middleware/mcp_slack.py`

```python
class SlackMCP:
    def __init__(self, bot_token):
        self.bot_token = bot_token
    
    async def send_message(self, channel, message):
        # Connect to Slack API
        # Send message
        # Return result
        pass
```

### Step 2: Register in Nexus

**File:** `middleware/agent.py`

```python
from mcp_slack import SlackMCP

class NexusAgent:
    def __init__(self):
        self.services = {
            'uber': UberMCP(),
            'jira': JiraMCP(),
            'calendar': GoogleCalendarMCP(),
            'slack': SlackMCP()  # Add new service
        }
    
    async def route_command(self, command_type, parameters):
        if command_type == 'slack_send':
            return await self.services['slack'].send_message(...)
```

### Step 3: Update Command Detector

**File:** `ride_detector.py`

```python
async def detect_trigger_and_destinations(segments):
    # Add logic to recognize Slack commands
    if "send message" in combined_text.lower():
        return True, "slack_send", parameters
```

### Step 4: Add Environment Variables

**File:** `.env`

```
SLACK_BOT_TOKEN=xoxb-your-token
```

### Step 5: Test

```
"Send a message to #general: Project is done"
Nexus recognizes command
Routes to Slack MCP
Message sent
Result returned
```

---

## Best Practices

### 1. Error Handling
- Always return structured responses
- Include error codes for debugging
- Log all failures

### 2. Authentication
- Store credentials in environment variables
- Never hardcode API keys
- Validate credentials on startup

### 3. Rate Limiting
- Respect service rate limits
- Implement exponential backoff
- Queue requests if needed

### 4. Logging
- Log all commands received
- Log all API calls
- Log all errors with context

### 5. Testing
- Test with mock data
- Test error scenarios
- Test authentication failures

---

## Service Integration Examples

### Booking an Uber

```
User: "Book an Uber to Pier 39"
         ↓
Nexus: Extracts pickup and destination
         ↓
Uber MCP: 
  1. Load saved session
  2. Open Uber website
  3. Fill pickup: "Ferry Building"
  4. Fill destination: "Pier 39"
  5. Select ride type: "UberX"
  6. Click "Request"
  7. Wait for confirmation
         ↓
Result: Driver "John", ETA "5 minutes"
         ↓
Confirmation sent to Omi
```

### Updating a Jira Ticket

```
User: "Update ticket PROJ-123 to done"
         ↓
Nexus: Extracts ticket ID and status
         ↓
Jira MCP:
  1. Connect to Jira API
  2. Find ticket PROJ-123
  3. Update status to "Done"
  4. Add timestamp
         ↓
Result: Ticket updated successfully
         ↓
Confirmation sent to Omi
```

### Scheduling a Meeting

```
User: "Schedule a meeting tomorrow at 2pm"
         ↓
Nexus: Extracts date and time
         ↓
Calendar MCP:
  1. Connect to Google Calendar
  2. Check availability at 2pm tomorrow
  3. Create event
  4. Add to calendar
         ↓
Result: Event created, ID "abc123"
         ↓
Confirmation sent to Omi
```

---

## Monitoring

### Health Checks

Each MCP server should implement:
```python
async def health_check(self):
    """Check if service is available"""
    try:
        # Test API connection
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}
```

### Metrics

Track:
- Commands executed
- Success rate
- Average execution time
- Error rate by type

---

## Summary

MCP Servers are the execution engines:
- Connect to external services
- Execute commands
- Return results
- Handle authentication
- Implement error handling

They're designed to be:
- **Modular** - Each service is independent
- **Extensible** - Easy to add new services
- **Reliable** - Proper error handling
- **Secure** - Credentials in environment

---

**Built with ❤️ for voice-activated productivity**
