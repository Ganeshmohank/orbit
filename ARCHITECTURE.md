# Architecture & Design 🏗️

Technical architecture and design decisions for the Omi Uber App.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Omi Device                              │
│  (Voice input → Transcription → Webhook)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Web Server                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  main.py - Request routing & endpoints              │  │
│  │  ├─ GET / (Home page)                               │  │
│  │  ├─ GET /auth (Authentication)                      │  │
│  │  ├─ POST /webhook (Voice booking)                   │  │
│  │  └─ GET /health (Health check)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────┼──────────────────────────────────┐   │
│  │                  │                                  │    │
│  ▼                  ▼                                  ▼    │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │auth_manager  │ │uber_automatio│ │ride_detector │        │
│ │              │ │              │ │              │        │
│ │• Login flow  │ │• Headless    │ │• Trigger     │        │
│ │• 2FA handle  │ │  browser     │ │  detection   │        │
│ │• Session mgmt│ │• Booking     │ │• Destination │        │
│ │• Validation  │ │• Error handle│ │  extraction  │        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ simple_storage.py - File-based persistence          │  │
│  │ ├─ User data (JSON)                                 │  │
│  │ ├─ Session storage (Playwright state)               │  │
│  │ └─ Booking history                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐          ┌──────────┐        ┌──────────┐
    │ Uber    │          │ OpenAI   │        │ File     │
    │ Website │          │ API      │        │ System   │
    │ (m.uber)│          │ (GPT)    │        │ (JSON)   │
    └─────────┘          └──────────┘        └──────────┘
```

## Component Architecture

### 1. main.py - FastAPI Application
**Responsibility**: HTTP request routing and endpoint handling

**Key Functions**:
- `home()` - Render home page with status
- `auth_page()` - Launch authentication flow
- `get_auth_status()` - Real-time auth status polling
- `submit_2fa_code()` - Handle 2FA code submission
- `webhook()` - Process voice transcripts
- `setup_completed()` - Check authentication status

**Design Pattern**: Async/await for non-blocking I/O

---

### 2. auth_manager.py - Authentication Manager
**Responsibility**: Uber authentication with 2FA support

**Key Classes**:
- `AuthManager` - Main authentication orchestrator

**Key Methods**:
- `start_login_flow()` - Initiate browser login
- `_detect_2fa_prompt()` - Identify 2FA screens
- `_wait_for_2fa_code()` - Wait for user code submission
- `_verify_2fa_and_complete()` - Fill and verify code
- `validate_session()` - Check if session still valid
- `submit_2fa_code()` - Receive code from user

**State Management**:
```python
active_browsers = {
    "uid": {
        "browser": Browser,
        "page": Page,
        "status": "waiting_login|waiting_2fa|completed",
        "2fa_code": None
    }
}
```

**Flow**:
1. Launch non-headless browser
2. Navigate to Uber login
3. Wait for login or 2FA
4. If 2FA: Pause and wait for code
5. Fill code and verify
6. Save session
7. Cleanup browser

---

### 3. uber_automation.py - Ride Booking
**Responsibility**: Automated Uber ride booking

**Key Classes**:
- `UberAutomation` - Booking orchestrator

**Key Methods**:
- `book_ride()` - Main booking function
- `_check_login_required()` - Validate session
- `_handle_security_challenges()` - Handle Uber security
- `_extract_ride_details()` - Parse confirmation page

**Flow**:
1. Load saved session
2. Launch headless browser
3. Navigate to Uber
4. Validate login status
5. Handle security challenges
6. Fill destination
7. Select suggestion
8. Click "Request UberX"
9. Extract driver & ETA
10. Return confirmation

---

### 4. ride_detector.py - AI-Powered Detection
**Responsibility**: Voice trigger and destination extraction

**Key Functions**:
- `is_trigger_phrase()` - Regex-based trigger detection
- `extract_destination()` - OpenAI-powered extraction
- `detect_trigger_and_destination()` - Combined detection

**Trigger Patterns**:
```python
patterns = [
    r"book\s+(?:an?\s+)?uber",
    r"get\s+(?:me\s+)?a\s+ride",
    r"call\s+(?:an?\s+)?uber",
    r"request\s+(?:an?\s+)?uber",
    r"order\s+(?:an?\s+)?uber",
]
```

**Destination Extraction**:
- Uses GPT-3.5-turbo
- Handles variations (SFO, San Francisco, airport)
- Cleans filler words
- Returns clean destination name

---

### 5. simple_storage.py - Persistence Layer
**Responsibility**: File-based data storage

**Key Functions**:
- `load_user_data()` - Load user JSON
- `save_user_data()` - Save user JSON
- `load_session()` - Load Playwright session
- `save_session()` - Save Playwright session
- `update_user_status()` - Update auth status
- `record_booking()` - Log completed booking

**File Structure**:
```
users/
  ├─ user123.json
  ├─ user456.json
  └─ ...

sessions/
  ├─ user123_uber_session.json
  ├─ user456_uber_session.json
  └─ ...
```

**User Data Schema**:
```json
{
  "uid": "user123",
  "uber_authenticated": true,
  "auth_status": "completed",
  "last_booking": {
    "destination": "SFO",
    "driver_name": "John",
    "eta": "5 min",
    "timestamp": "2024-01-01T12:00:00"
  },
  "remember_device": true,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

## Data Flow Diagrams

### Authentication Flow
```
User clicks "Connect Uber"
         │
         ▼
    /auth endpoint
         │
         ▼
    Launch browser (non-headless)
         │
         ▼
    Navigate to Uber login
         │
    ┌────┴────┐
    │          │
    ▼          ▼
  Login    2FA Required?
    │          │
    │          ▼
    │      Detect 2FA
    │          │
    │          ▼
    │      Update status: "waiting_2fa"
    │          │
    │          ▼
    │      Show code input UI
    │          │
    │          ▼
    │      Wait for /submit-2fa-code
    │          │
    │          ▼
    │      Fill code & verify
    │          │
    └────┬─────┘
         │
         ▼
    Check login success
         │
         ▼
    Save session (cookies + localStorage)
         │
         ▼
    Update status: "completed"
         │
         ▼
    Cleanup browser
         │
         ▼
    Redirect to home: "✅ Connected"
```

### Voice Booking Flow
```
Omi device captures voice
         │
         ▼
    Transcribe to text
         │
         ▼
    POST /webhook
         │
         ▼
    Detect trigger phrase
         │
    ┌────┴────┐
    │          │
   No        Yes
    │          │
    │          ▼
    │      Extract destination (OpenAI)
    │          │
    │          ▼
    │      Validate session
    │          │
    │    ┌─────┴─────┐
    │    │           │
    │  Valid      Expired
    │    │           │
    │    │           ▼
    │    │       Return: "Re-authenticate"
    │    │
    │    ▼
    │  Load session
    │    │
    │    ▼
    │  Launch headless browser
    │    │
    │    ▼
    │  Navigate to Uber
    │    │
    │    ▼
    │  Fill destination
    │    │
    │    ▼
    │  Click "Request UberX"
    │    │
    │    ▼
    │  Extract driver & ETA
    │    │
    │    ▼
    │  Record booking
    │    │
    │    ▼
    │  Return confirmation
    │
    ▼
Return: "No trigger" or "No destination"
```

---

## Technology Choices

### FastAPI
**Why**: 
- Async/await support for non-blocking I/O
- Automatic OpenAPI documentation
- Type hints for validation
- High performance
- Easy to deploy

### Playwright
**Why**:
- Modern browser automation
- Supports headless and visible modes
- Session persistence (storage_state)
- Better than Selenium for modern web
- Cross-browser support

### OpenAI API
**Why**:
- Accurate destination extraction
- Handles natural language variations
- Reliable and scalable
- Easy to integrate

### File-Based Storage
**Why**:
- Simple, no database needed
- Works on any platform
- Easy to backup/restore
- Suitable for small-scale deployment
- Can be migrated to database later

### Railway/Heroku
**Why**:
- Easy deployment
- Automatic scaling
- Built-in monitoring
- Environment variable management
- Good free tier options

---

## Security Considerations

### 1. Session Management
- Sessions saved as JSON files (not in code)
- Cookies and localStorage persisted
- Session validation before each booking
- Automatic cleanup on logout

### 2. 2FA Handling
- 2FA codes never logged
- Code validation (4-8 digits)
- Rate limiting (max 3 attempts)
- Timeout (5 minutes)
- "Remember device" checkbox checked

### 3. API Security
- Environment variables for secrets
- No hardcoded credentials
- Input validation on all endpoints
- Error messages don't expose sensitive data

### 4. Browser Automation
- Headless mode for bookings (less detectable)
- Visible mode only for auth (user control)
- Playwright stealth plugin ready
- User-agent rotation possible

---

## Performance Optimization

### 1. Async/Await
- Non-blocking I/O throughout
- Concurrent request handling
- Efficient resource usage

### 2. Session Caching
- Load session once per booking
- Reuse browser context
- Minimize API calls

### 3. Headless Mode
- Faster browser startup
- Lower resource usage
- Better for automated bookings

### 4. Background Tasks
- Booking happens in background
- Webhook returns immediately
- User not blocked

---

## Error Handling Strategy

### 1. Graceful Degradation
- Fallback options for each step
- Clear error messages
- User-friendly notifications

### 2. Retry Logic
- Automatic retry on timeout
- Manual retry option for users
- Exponential backoff possible

### 3. Logging
- All errors logged with context
- No sensitive data in logs
- Structured logging format

### 4. Recovery
- Session validation before booking
- Re-authentication if expired
- Cleanup on errors

---

## Scalability

### Current Limitations
- File-based storage (not suitable for >1000 users)
- Single server (no load balancing)
- In-memory browser state

### Future Improvements
- Migrate to database (PostgreSQL)
- Add Redis for session caching
- Implement load balancing
- Add monitoring/alerting
- Implement rate limiting

---

## Testing Strategy

### Unit Tests
- Trigger phrase detection
- Destination extraction
- Storage operations
- API endpoint responses

### Integration Tests
- Full authentication flow
- Booking flow
- Error handling
- Session management

### Manual Testing
- Browser automation
- 2FA handling
- Uber UI changes
- Edge cases

---

## Deployment Architecture

### Local Development
```
Developer Machine
├─ Python venv
├─ Playwright browsers
├─ FastAPI server
└─ File storage
```

### Docker Development
```
Docker Container
├─ Python 3.10
├─ Playwright (with Chromium)
├─ FastAPI server
└─ Volume mounts for storage
```

### Production (Railway)
```
Railway Container
├─ Python 3.10
├─ Playwright (installed at startup)
├─ FastAPI server
├─ Environment variables
└─ Persistent storage (if needed)
```

---

## Monitoring & Observability

### Metrics
- Authentication success rate
- Average booking time
- 2FA detection accuracy
- Session expiration rate
- Error frequency

### Logging
- Request/response logging
- Error logging with context
- Performance metrics
- User action tracking

### Health Checks
- `/health` endpoint
- Database connectivity
- External API availability
- Browser availability

---

## Future Enhancements

1. **Multi-Ride Support**
   - Book multiple rides in sequence
   - Handle ride cancellation

2. **Ride History**
   - Track all bookings
   - Show ride details
   - Integration with Uber account

3. **Advanced Destination Handling**
   - Favorite locations
   - Address book integration
   - Map selection

4. **Payment Integration**
   - Multiple payment methods
   - Wallet management
   - Receipt tracking

5. **Analytics**
   - Usage statistics
   - Popular destinations
   - Peak booking times

6. **Multi-Language Support**
   - Voice recognition in multiple languages
   - UI localization
   - Destination extraction in multiple languages

---

**Architecture designed for simplicity, reliability, and scalability! 🏗️**
