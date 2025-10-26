# Orbit - Agentic Workflow Automation System

Orbit is an intelligent agent designed to streamline daily workflows by integrating Jira, Google Calendar, and other productivity tools. It automates task management, meeting scheduling, progress tracking, and status reporting, enabling teams and individuals to focus on high-value work instead of manual coordination.

## Architecture Overview

Orbit consists of three core components:

### 1. **Omi** - Entry Point
Voice capture device that records conversations and sends voice commands to the system.
- Listens for voice commands like "Book an Uber", "Schedule a meeting", "Update my Jira tickets"
- Sends audio segments to the webhook for processing
- Receives task confirmation and status updates

### 2. **Nexus** - Middleware Agent
Intelligent agent that processes voice commands and communicates with external services.
- Parses voice commands using LLM
- Routes commands to appropriate MCP (Model Context Protocol) servers
- Maintains context from conversation flow
- Executes multi-step workflows

### 3. **MCP Servers** - Service Integrations
Extensible protocol for connecting to external services:
- **Jira** - Update tickets, create issues, manage sprints
- **Slack** - Send messages, create channels, post notifications
- **Teams** - Send messages, schedule meetings
- **Calendar** - Schedule meetings, check availability
- **PR Systems** - Create pull requests, manage code reviews
- *(More services can be added)*

## Project Structure

```
orbit/
├── main.py                    # FastAPI app with webhook and endpoints
├── ride_detector.py           # LLM-powered command extraction
├── simple_storage.py          # File-based user storage
├── auth_manager.py            # Authentication and session management
├── uber_automation.py         # Browser automation for ride booking
│
├── middleware/
│   ├── agent.py              # Nexus agent - MCP server communication
│   ├── mcp_client.py         # MCP protocol client
│   └── AGENTVERSE_README.md  # Nexus architecture documentation
│
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Multi-container setup
├── railway.toml              # Railway deployment config
└── README.md                 # This file
```

## Features

### Voice Command Processing
- **Sliding Window Collection** - Batches voice segments with 5 seconds of silence detection
- **LLM-Powered Extraction** - Understands natural language and corrects spelling mistakes
- **Multi-Service Routing** - Routes commands to appropriate MCP servers

### Supported Commands

**Ride Booking (via Uber automation)**
```
"Book an Uber to Pier 39"
"Get me a ride from SJSU to the airport"
"Call an Uber to downtown"
```

**Jira Integration (via Nexus + MCP)**
```
"Update my Jira ticket PROJ-123 to done"
"Create a new ticket for bug fix"
"Show me my assigned tickets"
```

**Calendar Integration (via Nexus + MCP)**
```
"Schedule a meeting with the team tomorrow at 2pm"
"Check my availability next week"
"Add this to my calendar"
```

**Extensible to more services:**
- Slack notifications
- Teams messaging
- PR creation and reviews
- And more...

## Setup

### 1. Install

```bash
git clone <repo>
cd orbit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
# Add your API keys:
# - OPENAI_API_KEY (for LLM processing)
# - JIRA_API_TOKEN (for Jira integration)
# - Other service credentials as needed
```

### 3. Run

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000`

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for LLM processing
- `JIRA_API_TOKEN` - Jira API token for ticket management
- `JIRA_DOMAIN` - Your Jira instance domain
- `PORT` - Server port (default: 8000)
- `AUTO_REQUEST` - Auto-book rides (default: false)

**Example .env:**
```
OPENAI_API_KEY=sk-proj-xxxxx
JIRA_API_TOKEN=your-jira-token
JIRA_DOMAIN=your-domain.atlassian.net
PORT=8000
AUTO_REQUEST=false
```

## API Endpoints

### GET `/`
Home page showing system status and authentication.

### GET `/auth`
Authentication flow for Uber account connection.

### POST `/webhook`
Main entry point for voice commands from Omi device.

**Request Body:**
```json
{
  "segments": [
    {
      "text": "Book an Uber to Pier 39",
      "speaker": "user"
    }
  ],
  "gps_lat": 37.7749,
  "gps_lon": -122.4194
}
```

**Response:**
```json
{
  "message": "Processing command...",
  "command_type": "ride_booking|jira_update|calendar_event",
  "status": "processing|completed|failed"
}
```

### GET `/health`
Health check endpoint.

## Workflow Examples

### Example 1: Voice-to-Uber Booking
```
User (via Omi): "Book an Uber to Pier 39"
         ↓
Webhook receives segments
         ↓
Sliding window waits for 5s silence
         ↓
LLM extracts: destination="Pier 39"
         ↓
Browser automation books ride
         ↓
Confirmation sent back to Omi
```

### Example 2: Voice-to-Jira Update
```
User (via Omi): "Update ticket PROJ-123 to done"
         ↓
Webhook receives segments
         ↓
LLM extracts: ticket="PROJ-123", status="done"
         ↓
Nexus agent connects to Jira MCP server
         ↓
Jira ticket updated
         ↓
Confirmation sent back to Omi
```

### Example 3: Voice-to-Calendar Event
```
User (via Omi): "Schedule a meeting tomorrow at 2pm"
         ↓
Webhook receives segments
         ↓
LLM extracts: event details from conversation context
         ↓
Nexus agent connects to Calendar MCP server
         ↓
Meeting scheduled
         ↓
Confirmation sent back to Omi
```

## Documentation

For detailed architecture and system design documentation, see:

- **START_HERE.md** - Quick start guide with system overview and architecture diagrams
- **ARCHITECTURE_UNIVERSE.md** - Complete system architecture and data flow
- **ARCHITECTURE_OMI.md** - Voice entry point (Omi device) documentation
- **ARCHITECTURE_NEXUS.md** - Middleware brain (Nexus agent) documentation
- **ARCHITECTURE_MCP.md** - Service integrations (Jira MCP, Google Calendar MCP, Uber Service)
- **ARCHITECTURE_GUIDE.md** - Navigation guide for all architecture documentation

## Nexus Agent (Middleware)

The Nexus agent is the intelligent middleware that:
- Maintains conversation context
- Routes commands to appropriate services
- Handles multi-step workflows
- Manages service integrations

See `middleware/AGENTVERSE_README.md` for detailed architecture.

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

### Heroku

```bash
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

## Security

- ✅ Session files stored locally (not in version control)
- ✅ API keys stored in environment variables
- ✅ HTTPS enforced in production
- ✅ Rate limiting on endpoints
- ✅ User authentication validation

## Extensibility

To add a new service:

1. Create an MCP server for the service
2. Add connection logic to `middleware/agent.py`
3. Update `ride_detector.py` to recognize commands for the service
4. Add environment variables for service credentials
5. Test with voice commands via the webhook

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black *.py
flake8 *.py
```

## License

MIT License - feel free to use and modify

---

**Built with ❤️ for voice-activated productivity**
