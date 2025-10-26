# API Reference 🔌

Complete API documentation for the Omi Uber App.

## Base URL

- **Local**: `http://localhost:8000`
- **Railway**: `https://your-project.railway.app`
- **Heroku**: `https://your-app-name.herokuapp.com`

---

## Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Purpose**: Check if the application is running

**Parameters**: None

**Response** (200 OK):
```json
{
  "status": "ok",
  "service": "omi-uber-app"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

**Use Case**: Deployment monitoring, health checks

---

### 2. Home Page

**Endpoint**: `GET /`

**Purpose**: Display app home page with authentication status

**Parameters**:
- `uid` (optional, query) - User ID (default: "default_user")

**Response** (200 OK): HTML page

**Response Content**:
- If authenticated: "✅ Uber Connected" with usage instructions
- If waiting for 2FA: "📱 Waiting for 2FA Verification"
- If not authenticated: "🔐 Connect Uber Account" button

**Example**:
```bash
curl http://localhost:8000/?uid=user123
```

**Use Case**: User-facing home page, status display

---

### 3. Start Authentication

**Endpoint**: `GET /auth`

**Purpose**: Launch the authentication flow

**Parameters**:
- `uid` (optional, query) - User ID (default: "default_user")

**Response** (200 OK): HTML page with authentication UI

**Flow**:
1. Opens browser with Uber login page
2. User enters credentials
3. If 2FA required, shows code input
4. Saves session after authentication
5. Redirects to home page

**Example**:
```bash
curl http://localhost:8000/auth?uid=user123
```

**Use Case**: Initial account connection, re-authentication

---

### 4. Get Authentication Status

**Endpoint**: `GET /auth-status`

**Purpose**: Get current authentication status (for real-time updates)

**Parameters**:
- `uid` (required, query) - User ID

**Response** (200 OK):
```json
{
  "status": "not_authenticated|waiting_login|waiting_2fa|completed|failed",
  "message": "Human-readable status message"
}
```

**Status Values**:
- `not_authenticated` - User hasn't authenticated yet
- `waiting_login` - Browser waiting for user to login
- `waiting_2fa` - 2FA code required
- `completed` - Authentication successful
- `failed` - Authentication failed

**Example**:
```bash
curl http://localhost:8000/auth-status?uid=user123
```

**Response Examples**:
```json
{
  "status": "waiting_2fa",
  "message": "📱 2FA code required"
}
```

```json
{
  "status": "completed",
  "message": "✅ Authentication successful!"
}
```

**Use Case**: Real-time status polling during authentication

---

### 5. Submit 2FA Code

**Endpoint**: `POST /submit-2fa-code`

**Purpose**: Submit 2FA code during authentication

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "uid": "user123",
  "code": "123456"
}
```

**Parameters**:
- `uid` (required) - User ID
- `code` (required) - 2FA code (4-8 digits)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Code submitted"
}
```

**Response** (200 OK - Error):
```json
{
  "success": false,
  "message": "Invalid code format"
}
```

**Error Cases**:
- Invalid code format (not 4-8 digits)
- No active authentication session
- Code already submitted

**Example**:
```bash
curl -X POST http://localhost:8000/submit-2fa-code \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user123",
    "code": "123456"
  }'
```

**Use Case**: 2FA code submission during authentication

---

### 6. Check Setup Completion

**Endpoint**: `GET /setup-completed`

**Purpose**: Check if user has completed authentication setup

**Parameters**:
- `uid` (required, query) - User ID

**Response** (200 OK):
```json
{
  "is_setup_completed": true,
  "auth_status": "completed"
}
```

**Response** (200 OK - Not Completed):
```json
{
  "is_setup_completed": false,
  "auth_status": "not_authenticated"
}
```

**Example**:
```bash
curl http://localhost:8000/setup-completed?uid=user123
```

**Use Case**: Omi app checking if user is authenticated

---

### 7. Voice Booking Webhook

**Endpoint**: `POST /webhook`

**Purpose**: Receive voice transcripts and book rides

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "uid": "user123",
  "segments": [
    {
      "text": "book an uber to san francisco airport",
      "speaker": "user"
    }
  ]
}
```

**Parameters**:
- `uid` (required) - User ID
- `segments` (required) - Array of voice segments
  - `text` (required) - Transcribed text
  - `speaker` (required) - Speaker identifier

**Response** (200 OK - Trigger Detected):
```json
{
  "message": "🚗 Booking Uber to San Francisco Airport...",
  "booked": true,
  "destination": "San Francisco Airport"
}
```

**Response** (200 OK - No Trigger):
```json
{
  "message": "No trigger phrase detected",
  "booked": false
}
```

**Response** (200 OK - No Destination):
```json
{
  "message": "⚠️ Could not extract destination from voice command",
  "booked": false
}
```

**Response** (200 OK - Not Authenticated):
```json
{
  "message": "⚠️ Please authenticate your Uber account first",
  "booked": false
}
```

**Response** (200 OK - Session Expired):
```json
{
  "message": "⚠️ Session expired. Please re-authenticate.",
  "booked": false
}
```

**Supported Trigger Phrases**:
- "Book an Uber to [destination]"
- "Get me a ride to [destination]"
- "Call an Uber to [destination]"
- "Request an Uber to [destination]"
- "Order an Uber to [destination]"

**Destination Examples**:
- "San Francisco Airport"
- "SFO"
- "Downtown"
- "123 Main Street"
- "The airport"
- "My house"

**Example**:
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user123",
    "segments": [
      {
        "text": "book an uber to downtown san francisco",
        "speaker": "user"
      }
    ]
  }'
```

**Response Example**:
```json
{
  "message": "🚗 Booking Uber to Downtown San Francisco...",
  "booked": true,
  "destination": "Downtown San Francisco"
}
```

**Use Case**: Voice booking from Omi device

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 404 Not Found
```json
{
  "detail": "Endpoint not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

### 2FA Endpoint
- **Limit**: 3 attempts per session
- **Timeout**: 5 minutes
- **Reset**: After successful verification or timeout

### Webhook Endpoint
- **Limit**: 100 requests per minute (recommended)
- **Timeout**: 15 seconds per request

---

## Authentication Flow Sequence

```
1. GET /auth?uid=user123
   ↓
2. Browser opens Uber login
   ↓
3. Poll GET /auth-status?uid=user123 (every 1 second)
   ↓
4. If status = "waiting_2fa":
   - Show code input UI
   - POST /submit-2fa-code with code
   ↓
5. Continue polling until status = "completed"
   ↓
6. Redirect to GET /?uid=user123
```

---

## Booking Flow Sequence

```
1. POST /webhook with voice transcript
   ↓
2. App detects trigger phrase
   ↓
3. App extracts destination
   ↓
4. App validates session
   ↓
5. App launches headless browser
   ↓
6. App fills destination and books ride
   ↓
7. Response: {"booked": true, "message": "..."}
```

---

## Data Models

### User Data
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

### Session Data
```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "abc123...",
      "domain": "uber.com",
      "path": "/",
      "expires": 1234567890
    }
  ],
  "localStorage": [
    {
      "name": "key",
      "value": "value"
    }
  ],
  "sessionStorage": [...],
  "origins": [...]
}
```

---

## Testing Endpoints

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Test Home Page
```bash
curl http://localhost:8000/
```

### Test Auth Status
```bash
curl http://localhost:8000/auth-status?uid=test_user
```

### Test Setup Completed
```bash
curl http://localhost:8000/setup-completed?uid=test_user
```

### Test Webhook (No Trigger)
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "segments": [{"text": "hello world", "speaker": "user"}]
  }'
```

### Test Webhook (With Trigger)
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "segments": [{"text": "book an uber to downtown", "speaker": "user"}]
  }'
```

### Test 2FA Code Submission
```bash
curl -X POST http://localhost:8000/submit-2fa-code \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "code": "123456"
  }'
```

---

## Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | All successful requests |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Internal error |

---

## Common Workflows

### Workflow 1: First-Time Setup
```bash
# 1. Check if authenticated
curl http://localhost:8000/setup-completed?uid=user123

# 2. If not, start auth
curl http://localhost:8000/auth?uid=user123

# 3. Poll for status
curl http://localhost:8000/auth-status?uid=user123

# 4. If 2FA needed, submit code
curl -X POST http://localhost:8000/submit-2fa-code \
  -H "Content-Type: application/json" \
  -d '{"uid": "user123", "code": "123456"}'

# 5. Poll until completed
curl http://localhost:8000/auth-status?uid=user123
```

### Workflow 2: Book a Ride
```bash
# 1. Send voice transcript
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user123",
    "segments": [{"text": "book an uber to downtown", "speaker": "user"}]
  }'

# Response: {"booked": true, "message": "🚗 Booked to Downtown..."}
```

### Workflow 3: Check Status
```bash
# Check if user is authenticated
curl http://localhost:8000/setup-completed?uid=user123

# Get current auth status
curl http://localhost:8000/auth-status?uid=user123

# Get home page
curl http://localhost:8000/?uid=user123
```

---

## Integration with Omi

### Required URLs
```
App Home URL:
GET https://your-app.railway.app/

Auth URL:
GET https://your-app.railway.app/auth

Setup Completed URL:
GET https://your-app.railway.app/setup-completed

Webhook URL:
POST https://your-app.railway.app/webhook
```

### Omi Configuration
1. Add the four URLs above to Omi app settings
2. Omi will call these endpoints as needed
3. User ID will be passed as `uid` parameter

### Omi Flow
```
1. Omi calls GET /setup-completed?uid=user123
2. If not completed, Omi shows "Connect Account" button
3. User clicks button → Omi opens GET /auth?uid=user123
4. User authenticates (including 2FA if needed)
5. Omi polls GET /auth-status?uid=user123
6. When completed, Omi shows "Connected"
7. User says voice command
8. Omi calls POST /webhook with transcript
9. App books ride and returns confirmation
```

---

## Performance

### Response Times
- Health check: < 50ms
- Home page: < 100ms
- Auth status: < 50ms
- Setup check: < 50ms
- Webhook (no trigger): < 100ms
- Destination extraction: 1-2 seconds (OpenAI)
- Ride booking: 10-15 seconds (browser automation)

### Optimization Tips
- Use polling interval of 1 second for auth status
- Implement exponential backoff for retries
- Cache user data locally when possible
- Use background tasks for booking

---

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Request/Response
```bash
# Add verbose flag to curl
curl -v http://localhost:8000/health

# Use httpie for better formatting
http http://localhost:8000/health
```

### Monitor Logs
```bash
# Railway
railway logs

# Heroku
heroku logs --tail

# Local
# Check console output
```

---

## Limits & Constraints

| Constraint | Value |
|-----------|-------|
| Max 2FA attempts | 3 per session |
| 2FA timeout | 5 minutes |
| Auth timeout | 5 minutes |
| Webhook timeout | 15 seconds |
| Code format | 4-8 digits |
| Max segments | Unlimited |
| Session validity | Until Uber session expires |

---

## Changelog

### Version 1.0.0
- Initial release
- Voice trigger detection
- 2FA support
- Session persistence
- Headless automation
- Omi integration

---

**API Reference Complete! 🎉**
