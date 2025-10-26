# Architecture Documentation Guide

Welcome to Orbit's architecture documentation. This guide explains how to navigate and understand the system.

---

## Documentation Structure

### 1. **ARCHITECTURE_UNIVERSE.md** - Start Here
The complete system overview. Read this first to understand:
- How all components work together
- The complete data flow
- Communication points between components
- The big picture of Orbit

**Best for:** Understanding the entire system

---

### 2. **ARCHITECTURE_OMI.md** - Voice Entry Point
Everything about Omi, the voice capture device:
- What Omi does
- How Omi communicates with Orbit
- Webhook format and data
- GPS coordinates
- Supported commands
- Setup and troubleshooting

**Best for:** Understanding voice input and Omi integration

---

### 3. **ARCHITECTURE_NEXUS.md** - Middleware Brain
Deep dive into Nexus, the intelligent middleware:
- How Nexus processes commands
- Sliding window segment collection
- LLM validation
- Command routing
- Service selection
- Error handling
- Extensibility

**Best for:** Understanding command processing and routing

---

### 4. **ARCHITECTURE_MCP.md** - Service Integrations
Complete guide to MCP Servers:
- What MCP servers do
- Available services (Uber, Jira, Calendar, Slack)
- Communication protocol
- How to add new services
- Error handling
- Best practices

**Best for:** Understanding service integrations and adding new services

---

## Reading Paths

### Path 1: I Want to Understand the Whole System
1. Read **ARCHITECTURE_UNIVERSE.md** (20 min)
2. Skim **ARCHITECTURE_OMI.md** (10 min)
3. Skim **ARCHITECTURE_NEXUS.md** (10 min)
4. Skim **ARCHITECTURE_MCP.md** (10 min)

**Total time:** ~50 minutes

---

### Path 2: I'm Integrating Omi
1. Read **ARCHITECTURE_OMI.md** (15 min)
2. Reference **ARCHITECTURE_UNIVERSE.md** for context (10 min)
3. Look at webhook examples (5 min)

**Total time:** ~30 minutes

---

### Path 3: I'm Adding a New Service
1. Read **ARCHITECTURE_MCP.md** (20 min)
2. Reference **ARCHITECTURE_NEXUS.md** for routing (10 min)
3. Look at examples (10 min)

**Total time:** ~40 minutes

---

### Path 4: I'm Debugging an Issue
1. Check **ARCHITECTURE_UNIVERSE.md** for the flow (5 min)
2. Find the component in relevant architecture file (10 min)
3. Look at error handling section (5 min)

**Total time:** ~20 minutes

---

## Key Concepts

### Sliding Window
Orbit collects voice segments for 5 seconds of silence before processing. This captures complete thoughts and handles natural speech pauses.

**See:** ARCHITECTURE_NEXUS.md → Phase 1

---

### LLM Validation
Every command is validated by OpenAI's LLM to ensure it's a real booking request and to extract locations.

**See:** ARCHITECTURE_NEXUS.md → Phase 2

---

### MCP Protocol
Services are integrated using the Model Context Protocol, which provides a standard interface for all service integrations.

**See:** ARCHITECTURE_MCP.md → Communication Protocol

---

### GPS Priority
When determining pickup location, the system prioritizes GPS coordinates from the device, then falls back to IP geolocation.

**See:** ARCHITECTURE_OMI.md → GPS Data

---

### Rate Limiting
To prevent accidental double-bookings, the system enforces a 30-second minimum between bookings per user.

**See:** ARCHITECTURE_NEXUS.md → Rate Limiting

---

## Component Relationships

```
┌─────────────────────────────────────────────────────────┐
│                    ORBIT UNIVERSE                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  OMI (Voice Input)                                      │
│  └─ Sends voice segments via webhook                   │
│     └─ Includes GPS coordinates (optional)             │
│                                                         │
│  NEXUS (Middleware)                                     │
│  └─ Collects segments (5 sec window)                   │
│  └─ Validates with LLM                                 │
│  └─ Extracts command details                           │
│  └─ Routes to appropriate MCP server                   │
│                                                         │
│  MCP SERVERS (Service Integrations)                     │
│  ├─ Uber MCP (book rides)                              │
│  ├─ Jira MCP (manage tickets)                          │
│  ├─ Calendar MCP (schedule meetings)                   │
│  └─ Slack MCP (send messages)                          │
│                                                         │
│  EXTERNAL SERVICES                                      │
│  ├─ Uber API                                           │
│  ├─ Jira API                                           │
│  ├─ Google Calendar API                                │
│  └─ Slack API                                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow Example

### Booking an Uber

```
1. User speaks: "Book an Uber to Pier 39"
   └─ See: ARCHITECTURE_OMI.md

2. Omi sends webhook:
   POST /webhook
   {
     "segments": [{"text": "Book an Uber to Pier 39", "speaker": "user"}],
     "gps_lat": 37.7749,
     "gps_lon": -122.4194
   }
   └─ See: ARCHITECTURE_OMI.md → Communication Protocol

3. Nexus collects segments (5 sec window)
   └─ See: ARCHITECTURE_NEXUS.md → Phase 1

4. Nexus validates with LLM
   Input: "Book an Uber to Pier 39"
   Output: is_trigger=true, destination="Pier 39"
   └─ See: ARCHITECTURE_NEXUS.md → Phase 2

5. Nexus determines pickup location
   GPS: (37.7749, -122.4194)
   Landmark: "Ferry Building"
   └─ See: ARCHITECTURE_NEXUS.md → Phase 4

6. Nexus validates authentication
   └─ See: ARCHITECTURE_NEXUS.md → Phase 5

7. Nexus routes to Uber MCP
   └─ See: ARCHITECTURE_MCP.md → Uber MCP

8. Uber MCP executes booking
   - Opens Uber website
   - Fills pickup: "Ferry Building"
   - Fills destination: "Pier 39"
   - Clicks "Request"
   └─ See: ARCHITECTURE_MCP.md → Service Integration Examples

9. Result returned
   {
     "success": true,
     "driver": "John",
     "eta": "5 minutes"
   }
   └─ See: ARCHITECTURE_MCP.md → Communication Protocol

10. Confirmation sent to Omi
    └─ See: ARCHITECTURE_UNIVERSE.md → Step 7
```

---

## File Locations

### Architecture Documentation
```
/ARCHITECTURE_UNIVERSE.md    - Complete system overview
/ARCHITECTURE_OMI.md         - Voice entry point
/ARCHITECTURE_NEXUS.md       - Middleware brain
/ARCHITECTURE_MCP.md         - Service integrations
/ARCHITECTURE_GUIDE.md       - This file
```

### Main Code
```
/main.py                     - FastAPI app (webhook handler)
/middleware/agent.py         - Nexus agent
/ride_detector.py            - Command validation & extraction
/uber_automation.py          - Browser automation
/auth_manager.py             - Authentication
/simple_storage.py           - File storage
```

### Configuration
```
/.env.example                - Environment variables template
/requirements.txt            - Python dependencies
/Dockerfile                  - Docker configuration
/docker-compose.yml          - Multi-container setup
```

---

## Common Questions

### Q: How do I add a new service?
**A:** Read ARCHITECTURE_MCP.md → Adding a New MCP Server

---

### Q: How does Omi send commands?
**A:** Read ARCHITECTURE_OMI.md → Communication Protocol

---

### Q: How does the system validate commands?
**A:** Read ARCHITECTURE_NEXUS.md → Phase 2: Validate with LLM

---

### Q: How are pickup locations determined?
**A:** Read ARCHITECTURE_NEXUS.md → Phase 4: Determine Pickup Location

---

### Q: What's the sliding window?
**A:** Read ARCHITECTURE_NEXUS.md → Phase 1: Collect Voice Segments

---

### Q: How do I debug an issue?
**A:** Read ARCHITECTURE_UNIVERSE.md → Error Handling

---

## Key Files to Understand

### For Voice Integration
- `main.py` - Webhook endpoint
- `ARCHITECTURE_OMI.md` - Omi protocol

### For Command Processing
- `ride_detector.py` - LLM validation
- `ARCHITECTURE_NEXUS.md` - Processing pipeline

### For Service Integration
- `middleware/agent.py` - Service routing
- `ARCHITECTURE_MCP.md` - MCP protocol

### For Authentication
- `auth_manager.py` - Session management
- `ARCHITECTURE_UNIVERSE.md` - Auth flow

---

## Architecture Principles

### 1. Modularity
Each component (Omi, Nexus, MCP) is independent and can be developed separately.

---

### 2. Extensibility
New services can be added without modifying core logic. Just create a new MCP server.

---

### 3. Simplicity
No unnecessary complexity. Each component has a single, clear responsibility.

---

### 4. Reliability
Comprehensive error handling and logging at every step.

---

### 5. Security
Credentials stored in environment variables, never hardcoded.

---

## Deployment

### Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

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

---

## Getting Help

### Understand the System
→ Read ARCHITECTURE_UNIVERSE.md

### Integrate Omi
→ Read ARCHITECTURE_OMI.md

### Add a Service
→ Read ARCHITECTURE_MCP.md

### Debug an Issue
→ Check relevant architecture file + logs

### Extend Functionality
→ Read ARCHITECTURE_NEXUS.md

---

## Next Steps

1. **Start with ARCHITECTURE_UNIVERSE.md** to understand the big picture
2. **Choose your path** based on what you want to do
3. **Reference specific files** as needed
4. **Check the code** for implementation details

---

## Summary

Orbit's architecture is organized into four clear layers:

1. **Omi** - Captures voice commands
2. **Nexus** - Processes and routes commands
3. **MCP Servers** - Execute actions on services
4. **External Services** - Uber, Jira, Calendar, Slack, etc.

Each layer is documented separately, but they work together seamlessly to turn voice commands into actions.

---

**Built with ❤️ for voice-activated productivity**
