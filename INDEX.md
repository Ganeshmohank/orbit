# Omi Uber App - Complete Index 📚

Welcome to the Omi Uber App! This is your complete guide to all project files and documentation.

## 🚀 Quick Start

**New to this project?** Start here:

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Understand what this does
3. **[README.md](README.md)** - Full documentation

---

## 📁 Project Files

### Core Application Files

#### `main.py` (23 KB)
**FastAPI web application with all endpoints**

Contains:
- GET `/` - Home page with status
- GET `/auth` - Authentication flow
- GET `/auth-status` - Real-time status polling
- POST `/submit-2fa-code` - 2FA code submission
- POST `/webhook` - Voice booking endpoint
- GET `/setup-completed` - Setup status check
- GET `/health` - Health check

**Key Features**:
- Async/await throughout
- Real-time HTML UI updates
- Background task processing
- Comprehensive error handling

---

#### `auth_manager.py` (10.5 KB)
**Authentication manager with 2FA support**

Contains:
- `AuthManager` class - Main orchestrator
- 2FA detection and handling
- Session persistence
- Browser lifecycle management
- Active browser state tracking

**Key Features**:
- Non-headless browser for auth
- Automatic 2FA detection
- Code submission handling
- Session validation
- Cleanup on completion

---

#### `uber_automation.py` (7 KB)
**Playwright browser automation for ride booking**

Contains:
- `UberAutomation` class - Booking orchestrator
- Headless browser automation
- Session loading and validation
- Security challenge handling
- Ride details extraction

**Key Features**:
- Headless mode for bookings
- Session reuse
- Error recovery
- Driver/ETA extraction
- Booking confirmation

---

#### `ride_detector.py` (1.8 KB)
**AI-powered voice trigger and destination detection**

Contains:
- `is_trigger_phrase()` - Regex-based detection
- `extract_destination()` - OpenAI-powered extraction
- `detect_trigger_and_destination()` - Combined detection

**Supported Phrases**:
- "Book an Uber to [destination]"
- "Get me a ride to [destination]"
- "Call an Uber to [destination]"
- "Request an Uber to [destination]"
- "Order an Uber to [destination]"

---

#### `simple_storage.py` (2.9 KB)
**File-based user data and session storage**

Contains:
- User data management (JSON)
- Session storage (Playwright state)
- Authentication status tracking
- Booking history recording

**Storage Locations**:
- User data: `users/{uid}.json`
- Sessions: `sessions/{uid}_uber_session.json`

---

### Configuration Files

#### `requirements.txt` (120 bytes)
**Python dependencies**

Includes:
- fastapi==0.104.1
- uvicorn==0.24.0
- playwright==1.40.0
- openai==1.3.0
- python-dotenv==1.0.0
- pydantic==2.5.0
- aiofiles==23.2.1

---

#### `.env.example` (101 bytes)
**Environment variables template**

Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `PORT` - Server port (optional, default 8000)
- `PLAYWRIGHT_BROWSERS_PATH` - Browser cache path (optional)

---

#### `Dockerfile` (801 bytes)
**Docker container configuration**

Features:
- Python 3.10-slim base image
- Playwright Chromium installation
- Health check endpoint
- Port 8000 exposed

---

#### `docker-compose.yml` (475 bytes)
**Docker Compose for local development**

Features:
- Service definition
- Volume mounts for storage
- Environment variable support
- Health check configuration

---

#### `railway.toml` (277 bytes)
**Railway deployment configuration**

Features:
- Nixpacks builder
- Python provider
- Playwright installation
- Environment variables

---

#### `Procfile` (81 bytes)
**Heroku/Railway process file**

Command:
```
playwright install chromium && uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

#### `.gitignore` (240 bytes)
**Git ignore rules**

Ignores:
- Python cache (`__pycache__/`)
- Virtual environment (`venv/`)
- Environment files (`.env`)
- Session files (`sessions/`)
- User data (`users/`)

---

### Setup & Deployment

#### `setup.sh` (1.5 KB)
**Automated setup script**

Does:
1. Checks Python version
2. Creates virtual environment
3. Installs dependencies
4. Installs Playwright browsers
5. Creates storage directories
6. Sets up .env file

**Usage**:
```bash
./setup.sh
source venv/bin/activate
```

---

### Testing

#### `test_app.py` (9 KB)
**Comprehensive test suite**

Tests:
- Health check endpoint
- Home page rendering
- Authentication endpoints
- 2FA code submission
- Webhook processing
- Storage operations
- Trigger phrase detection
- Integration flows

**Run Tests**:
```bash
pytest test_app.py -v
```

---

## 📖 Documentation Files

### Getting Started

#### [QUICKSTART.md](QUICKSTART.md) (4.4 KB)
**5-minute setup and deployment guide**

Covers:
- Local development setup
- Docker development
- Testing the app
- Railway deployment
- Heroku deployment
- Troubleshooting

**Best for**: First-time users

---

#### [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) (12.9 KB)
**Complete project overview**

Covers:
- What this project does
- Key features
- Technology stack
- API endpoints
- Authentication flow
- File storage
- Deployment options
- Configuration
- Testing
- Security
- Limitations
- Future enhancements

**Best for**: Understanding the project

---

### Detailed Documentation

#### [README.md](README.md) (8.9 KB)
**Full technical documentation**

Covers:
- Features overview
- Tech stack
- Installation instructions
- Configuration
- API endpoints (detailed)
- Authentication flow
- 2FA handling
- Voice trigger detection
- Deployment (Railway, Heroku, Docker)
- File storage
- Error handling
- Development
- Security
- Limitations
- Support

**Best for**: Reference and troubleshooting

---

#### [OMI_INTEGRATION.md](OMI_INTEGRATION.md) (9.6 KB)
**Omi platform integration guide**

Covers:
- Required endpoints
- Omi app configuration
- User ID handling
- Authentication flow
- 2FA handling
- Session management
- Error handling
- Testing
- Deployment checklist
- Monitoring
- Troubleshooting

**Best for**: Integrating with Omi device

---

#### [ARCHITECTURE.md](ARCHITECTURE.md) (15.2 KB)
**Technical architecture and design**

Covers:
- System overview diagram
- Component architecture
- Data flow diagrams
- Technology choices
- Security considerations
- Performance optimization
- Error handling strategy
- Scalability
- Testing strategy
- Deployment architecture
- Monitoring
- Future enhancements

**Best for**: Understanding system design

---

#### [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) (10.3 KB)
**Complete deployment checklist**

Covers:
- Pre-deployment setup
- Railway deployment
- Heroku deployment
- Docker deployment
- Omi integration setup
- Security checklist
- Performance checklist
- Monitoring setup
- Post-deployment verification
- Rollback plan
- Maintenance tasks
- Sign-off

**Best for**: Deploying to production

---

## 🎯 How to Use This Project

### For Development
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `./setup.sh`
3. Start coding with `uvicorn main:app --reload`
4. Run tests with `pytest test_app.py -v`

### For Understanding
1. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. Review [ARCHITECTURE.md](ARCHITECTURE.md)
3. Check [README.md](README.md) for details

### For Deployment
1. Follow [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. Use [QUICKSTART.md](QUICKSTART.md) for quick deployment
3. Reference [OMI_INTEGRATION.md](OMI_INTEGRATION.md) for Omi setup

### For Integration
1. Read [OMI_INTEGRATION.md](OMI_INTEGRATION.md)
2. Configure URLs in Omi app
3. Test endpoints manually
4. Monitor logs

---

## 📊 File Statistics

| File | Size | Purpose |
|------|------|---------|
| main.py | 23 KB | FastAPI application |
| auth_manager.py | 10.5 KB | Authentication |
| uber_automation.py | 7 KB | Ride booking |
| ride_detector.py | 1.8 KB | Trigger detection |
| simple_storage.py | 2.9 KB | Data storage |
| test_app.py | 9 KB | Tests |
| README.md | 8.9 KB | Documentation |
| QUICKSTART.md | 4.4 KB | Quick start |
| PROJECT_SUMMARY.md | 12.9 KB | Overview |
| OMI_INTEGRATION.md | 9.6 KB | Omi guide |
| ARCHITECTURE.md | 15.2 KB | Architecture |
| DEPLOYMENT_CHECKLIST.md | 10.3 KB | Deployment |
| **Total** | **~115 KB** | **Complete project** |

---

## 🔑 Key Concepts

### Voice-Activated Booking
User says "Book an Uber to [destination]" → App detects trigger → Extracts destination → Books ride automatically

### One-Time Authentication
User authenticates once → Session saved → Never login again → Reuse session for all bookings

### 2FA Support
Uber asks for 2FA → App detects → Shows code input → User enters code → App verifies → Continues booking

### Session Persistence
Playwright storage state saved → Includes cookies + localStorage → Loaded for each booking → Validated before use

### Headless Automation
Auth: Non-headless (user sees browser) → Booking: Headless (fast, invisible) → Efficient and user-friendly

---

## 🚀 Deployment Paths

### Path 1: Railway (Recommended)
```
Local Development
    ↓
Push to GitHub
    ↓
Connect to Railway
    ↓
Deploy
    ↓
Configure in Omi
    ↓
Test voice commands
```

### Path 2: Heroku
```
Local Development
    ↓
Push to GitHub
    ↓
Connect to Heroku
    ↓
Deploy
    ↓
Configure in Omi
    ↓
Test voice commands
```

### Path 3: Docker
```
Local Development
    ↓
Build Docker image
    ↓
Push to registry
    ↓
Deploy to cloud
    ↓
Configure in Omi
    ↓
Test voice commands
```

---

## 📋 Common Tasks

### Setup Development Environment
```bash
./setup.sh
source venv/bin/activate
```

### Run Locally
```bash
uvicorn main:app --reload
```

### Run Tests
```bash
pytest test_app.py -v
```

### Deploy to Railway
```bash
railway login
railway init
railway variables set OPENAI_API_KEY=your_key
railway up
```

### Deploy to Heroku
```bash
heroku login
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

### Run with Docker
```bash
docker-compose up --build
```

### Test Endpoints
```bash
curl http://localhost:8000/health
curl http://localhost:8000/
curl http://localhost:8000/auth-status?uid=test
```

---

## 🔍 Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| OPENAI_API_KEY not set | See [QUICKSTART.md](QUICKSTART.md#troubleshooting) |
| Playwright not installed | See [README.md](README.md#installation) |
| Port 8000 in use | See [QUICKSTART.md](QUICKSTART.md#troubleshooting) |
| Authentication fails | See [README.md](README.md#error-handling) |
| 2FA not detected | See [ARCHITECTURE.md](ARCHITECTURE.md#2fa-handling) |
| Deployment issues | See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md#rollback-plan) |

---

## 📚 Learning Resources

### Understanding the Project
1. Start with [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design
3. Check [README.md](README.md) for details

### Setting Up
1. Follow [QUICKSTART.md](QUICKSTART.md)
2. Run `./setup.sh`
3. Test locally

### Deploying
1. Use [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. Follow [QUICKSTART.md](QUICKSTART.md) deployment section
3. Configure in Omi using [OMI_INTEGRATION.md](OMI_INTEGRATION.md)

### Integrating with Omi
1. Read [OMI_INTEGRATION.md](OMI_INTEGRATION.md)
2. Deploy app first
3. Configure URLs in Omi app
4. Test voice commands

---

## 🎓 Code Structure

```
omi-uber-app/
├── Core Application
│   ├── main.py              # FastAPI endpoints
│   ├── auth_manager.py      # 2FA & authentication
│   ├── uber_automation.py   # Ride booking
│   ├── ride_detector.py     # Trigger detection
│   └── simple_storage.py    # Data storage
│
├── Configuration
│   ├── requirements.txt     # Dependencies
│   ├── .env.example         # Environment template
│   ├── railway.toml         # Railway config
│   ├── Procfile             # Process definition
│   ├── Dockerfile           # Docker config
│   └── docker-compose.yml   # Docker Compose
│
├── Setup & Testing
│   ├── setup.sh             # Setup script
│   └── test_app.py          # Test suite
│
└── Documentation
    ├── INDEX.md             # This file
    ├── README.md            # Full documentation
    ├── QUICKSTART.md        # Quick start
    ├── PROJECT_SUMMARY.md   # Overview
    ├── OMI_INTEGRATION.md   # Omi guide
    ├── ARCHITECTURE.md      # Architecture
    └── DEPLOYMENT_CHECKLIST.md  # Deployment
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] `./setup.sh` completes successfully
- [ ] `uvicorn main:app --reload` starts without errors
- [ ] `curl http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] `curl http://localhost:8000/` loads home page
- [ ] `pytest test_app.py -v` passes all tests
- [ ] Manual authentication flow works
- [ ] 2FA code submission works
- [ ] Webhook accepts requests
- [ ] All documentation is readable

---

## 🆘 Getting Help

### Documentation
- Check the relevant documentation file above
- Search for your issue in [README.md](README.md#error-handling)
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design questions

### Testing
- Run `pytest test_app.py -v` for test examples
- Check test_app.py for usage patterns
- Review logs for error messages

### Deployment
- Follow [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- Check [QUICKSTART.md](QUICKSTART.md#troubleshooting)
- Review deployment logs

### Integration
- Read [OMI_INTEGRATION.md](OMI_INTEGRATION.md)
- Test endpoints manually
- Check app logs

---

## 📞 Support Resources

- **GitHub**: [BasedHardware/omi](https://github.com/BasedHardware/omi)
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Playwright**: [playwright.dev](https://playwright.dev)
- **OpenAI**: [platform.openai.com](https://platform.openai.com)
- **Railway**: [railway.app](https://railway.app)
- **Heroku**: [heroku.com](https://heroku.com)

---

## 🎉 Next Steps

1. **Read** [QUICKSTART.md](QUICKSTART.md) (5 min)
2. **Setup** with `./setup.sh` (2 min)
3. **Run** with `uvicorn main:app --reload` (1 min)
4. **Test** at http://localhost:8000 (5 min)
5. **Deploy** using [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) (15 min)
6. **Integrate** with Omi using [OMI_INTEGRATION.md](OMI_INTEGRATION.md) (10 min)
7. **Test** voice commands (5 min)

**Total time: ~40 minutes from zero to working voice-activated Uber booking! 🚀**

---

**Welcome to the Omi Uber App! Happy coding! 🎉**
