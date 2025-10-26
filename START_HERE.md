# START HERE - Orbit Architecture Documentation

Welcome to Orbit! This is your entry point to understanding the entire system.

---

## What is Orbit?

Orbit is an intelligent agent designed to streamline daily workflows by integrating Jira, Google Calendar, and other productivity tools. It automates task management, meeting scheduling, progress tracking, and status reporting.

**Example:**
```
You: "Update ticket PROJ-123 to done"
Orbit: Updates the ticket in Jira
You: "Schedule a meeting tomorrow at 2pm"
Orbit: Creates the meeting in Google Calendar
```

---

## The Three Components

### 1. **Omi** - Voice Interface
- Listens to what you say
- Sends voice commands to Orbit
- Provides GPS location

### 2. **Nexus** - Middleware Brain
- Understands what you want
- Routes commands to the right service
- Executes the action

### 3. **MCP Servers** - Service Connectors
- Connect to Jira, Google Calendar, Uber, etc.
- Execute commands on those services
- Return results

---

## Quick Visual

```
┌─────────────────────────────────────────────────────┐
│  You speak: "Book an Uber to Pier 39"              │
└──────────────────┬────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Omi (Voice Device)  │
        │  - Records voice     │
        │  - Sends to Orbit    │
        └──────────┬───────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Nexus (Brain)       │
        │  - Understands       │
        │  - Validates         │
        │  - Routes            │
        └──────────┬───────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Uber MCP Server     │
        │  - Books ride        │
        │  - Returns result    │
        └──────────┬───────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Uber API            │
        │  - Executes booking  │
        └──────────┬───────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Confirmation        │
        │  Driver: John        │
        │  ETA: 5 minutes      │
        └──────────────────────┘
```

---

## Documentation Files

### **ARCHITECTURE_UNIVERSE.md** (Start Here!)
**The complete system overview**
- How everything works together
- Complete data flow
- All communication points
- Processing pipeline

**Read this first to understand the big picture**

---

### **ARCHITECTURE_OMI.md**
**Voice entry point documentation**
- What Omi does
- How Omi communicates
- Webhook format
- GPS coordinates
- Setup and troubleshooting

**Read this if you're integrating Omi**

---

### **ARCHITECTURE_NEXUS.md**
**Middleware brain documentation**
- How Nexus processes commands
- Processing pipeline
- Command validation
- Service routing
- Adding new services

**Read this if you're extending Nexus**

---

### **ARCHITECTURE_MCP.md**
**Service integration documentation**
- What MCP servers do
- Available services (Uber, Jira, Google Calendar)
- Communication protocol
- How to add new services
- Best practices

**Read this if you're adding a new service**

---

### **ARCHITECTURE_GUIDE.md**
**Navigation guide**
- How to navigate all docs
- Reading paths for different goals
- Key concepts
- Common questions
- File locations

**Read this to find what you need**

---

## Quick Start Paths

### 🎯 Path 1: Understand Everything
1. Read **ARCHITECTURE_UNIVERSE.md** (20 min)
2. Skim other files as needed

**Result:** You understand the entire system

---

### 🎯 Path 2: Integrate Omi
1. Read **ARCHITECTURE_OMI.md** (15 min)
2. Reference **ARCHITECTURE_UNIVERSE.md** (10 min)

**Result:** You can integrate Omi with Orbit

---

### 🎯 Path 3: Add a New Service
1. Read **ARCHITECTURE_MCP.md** (20 min)
2. Reference **ARCHITECTURE_NEXUS.md** (10 min)

**Result:** You can add Slack, Teams, or any service

---

### 🎯 Path 4: Debug an Issue
1. Check **ARCHITECTURE_UNIVERSE.md** (5 min)
2. Find the component in relevant file (10 min)
3. Look at error handling (5 min)

**Result:** You can fix the issue

---

## Key Concepts (Simple Explanations)

### Sliding Window
Orbit waits for 5 seconds of silence before processing your command. This captures your complete thought.

**Example:**
```
t=0s: You say "Book an Uber"
      └─ Orbit starts waiting

t=2s: You say "to Pier 39"
      └─ Orbit restarts waiting

t=7s: 5 seconds of silence
      └─ Orbit processes: "Book an Uber to Pier 39"
```

---

### LLM Validation
Every command is checked by AI to make sure it's a real booking request.

**Example:**
```
Input: "Book an Uber to Pier 39"
LLM: "Yes, this is a booking request"
Output: destination="Pier 39"

Input: "Book an Uber to my office"
LLM: "No, 'my office' is too generic"
Output: Rejected
```

---

### MCP Protocol
A standard way to connect to any service (Uber, Jira, Slack, etc.)

**Example:**
```
Command: "Update ticket PROJ-123 to done"
└─ Nexus routes to Jira MCP
└─ Jira MCP connects to Jira API
└─ Ticket updated
```

---

### GPS Priority
When determining where you are:
1. Device GPS (most accurate)
2. IP geolocation (less accurate)
3. Hardcoded location (fallback)

---

## File Structure

```
orbit/
├── README.md                      # Main project docs
│
├── ARCHITECTURE_UNIVERSE.md       # Complete system overview ⭐ START HERE
├── ARCHITECTURE_OMI.md            # Voice entry point
├── ARCHITECTURE_NEXUS.md          # Middleware brain
├── ARCHITECTURE_MCP.md            # Service integrations
├── ARCHITECTURE_GUIDE.md          # Navigation guide
├── START_HERE.md                  # This file
│
├── main.py                        # FastAPI app (webhook handler)
├── middleware/
│   ├── agent.py                  # Nexus agent
│   └── AGENTVERSE_README.md      # Meeting analysis details
│
├── ride_detector.py              # Command validation
├── uber_automation.py            # Browser automation
├── auth_manager.py               # Authentication
├── simple_storage.py             # File storage
│
├── requirements.txt              # Dependencies
├── .env.example                  # Environment template
├── Dockerfile                    # Docker config
└── docker-compose.yml            # Multi-container setup
```

---

## What Each File Does

### Code Files

- **main.py** - Receives webhook from Omi, manages authentication
- **middleware/agent.py** - Nexus brain, processes commands
- **ride_detector.py** - LLM validation, location extraction
- **uber_automation.py** - Browser automation for booking
- **auth_manager.py** - Handles Uber authentication
- **simple_storage.py** - Saves user data and sessions

### Configuration Files

- **requirements.txt** - Python packages needed
- **.env.example** - Environment variables template
- **Dockerfile** - How to run in Docker
- **docker-compose.yml** - Multi-container setup

### Documentation Files

- **README.md** - Project overview
- **ARCHITECTURE_*.md** - Detailed architecture docs
- **START_HERE.md** - This file

---

## Next Steps

### 1. Understand the System
Read **ARCHITECTURE_UNIVERSE.md** (20 minutes)

### 2. Choose Your Goal
- Integrating Omi? → Read **ARCHITECTURE_OMI.md**
- Adding a service? → Read **ARCHITECTURE_MCP.md**
- Extending Nexus? → Read **ARCHITECTURE_NEXUS.md**
- Need help? → Read **ARCHITECTURE_GUIDE.md**

### 3. Check the Code
Look at the relevant Python files for implementation details

### 4. Deploy
Use Docker, Railway, or local development setup

---

## Common Questions

### Q: How do I get started?
**A:** Read ARCHITECTURE_UNIVERSE.md first

### Q: How do I add Slack integration?
**A:** Read ARCHITECTURE_MCP.md → Adding a New MCP Server

### Q: How does Omi send commands?
**A:** Read ARCHITECTURE_OMI.md → Communication Protocol

### Q: How does the system validate commands?
**A:** Read ARCHITECTURE_NEXUS.md → Phase 2

### Q: What's the sliding window?
**A:** Read ARCHITECTURE_NEXUS.md → Phase 1

---

## Architecture at a Glance

```
Voice Input (Omi)
      ↓
Segment Collection (5 sec window)
      ↓
LLM Validation (Is this a real command?)
      ↓
Command Extraction (What do you want?)
      ↓
Service Routing (Which service?)
      ↓
Authentication Check (Are you logged in?)
      ↓
Execute Action (Book ride, update ticket, etc.)
      ↓
Return Result (Confirmation to Omi)
```

---

## Key Features

✅ **Voice-Activated** - Just speak your command
✅ **Multi-Service** - Uber, Jira, Calendar, Slack, and more
✅ **Intelligent** - LLM validates and understands natural language
✅ **Extensible** - Easy to add new services
✅ **Secure** - Credentials in environment variables
✅ **Reliable** - Comprehensive error handling
✅ **Well-Documented** - Clear, jargon-free documentation

---

## Getting Help

### For System Understanding
→ **ARCHITECTURE_UNIVERSE.md**

### For Omi Integration
→ **ARCHITECTURE_OMI.md**

### For Service Addition
→ **ARCHITECTURE_MCP.md**

### For Navigation Help
→ **ARCHITECTURE_GUIDE.md**

### For Nexus Details
→ **ARCHITECTURE_NEXUS.md**

---

## Summary

Orbit is a simple, elegant system:

1. **Omi** listens to your voice
2. **Nexus** understands what you want
3. **MCP Servers** execute the action
4. **Result** comes back to you

Everything is documented clearly, with no jargon. Start with ARCHITECTURE_UNIVERSE.md and explore from there.

---

## Ready to Begin?

👉 **Read ARCHITECTURE_UNIVERSE.md next**

It will give you the complete picture of how Orbit works.

---

**Built with ❤️ for voice-activated productivity**
