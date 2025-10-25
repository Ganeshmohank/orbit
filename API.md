# API Reference - Omi Uber App

Complete API documentation for all endpoints.

## Base URL
```
http://localhost:8000  (Development)
https://your-domain.com (Production)
```

## Authentication

All endpoints use the `uid` parameter to identify users. No API key required for local testing.

---

## Endpoints

### 1. GET `/`
**Home Page**

Returns the main dashboard with authentication status.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uid | string | No | default_user | User identifier |

**Response:**
```html
HTML page with:
- Authentication status
- Connect/Disconnect button
- Usage instructions
- Booking history
```

**Example:**
```bash
curl http://localhost:8000/?uid=user123
```

---

### 2. GET `/auth`
**Start Authentication Flow**

Initiates the Uber authentication process.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uid | string | No | default_user | User identifier |

**Response:**
```html
Browser opens Uber login page
User completes authentication
Redirects to home page on success
```

**Example:**
```bash
curl http://localhost:8000/auth?uid=user123
```

**Flow:**
1. Opens Uber.com in browser
2. Detects login page
3. If 2FA required, shows code input
4. Saves session after authentication
5. Redirects to home page

---

### 3. GET `/auth-status`
**Check Authentication Status**

Get current authentication status for real-time updates.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uid | string | Yes | - | User identifier |

**Response:**
```json
{
  "status": "completed|waiting_2fa|failed|waiting_login",
  "message": "Human-readable status message"
}
```

**Status Values:**
- `completed` - User is authenticated
- `waiting_2fa` - Waiting for 2FA code
- `failed` - Authentication failed
- `waiting_login` - Waiting for login

**Example:**
```bash
curl http://localhost:8000/auth-status?uid=user123

# Response
{
  "status": "completed",
  "message": "✅ Authenticated"
}
```

---

### 4. POST `/submit-2fa-code`
**Submit 2FA Code**

Submit a 2FA code during authentication.

**Request Body:**
```json
{
  "uid": "user123",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Code submitted successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/submit-2fa-code \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user123",
    "code": "123456"
  }'
```

---

### 5. GET `/setup-completed`
**Check Setup Status**

Verify if user has completed authentication setup.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uid | string | Yes | - | User identifier |

**Response:**
```json
{
  "is_setup_completed": true,
  "auth_status": "completed"
}
```

**Example:**
```bash
curl http://localhost:8000/setup-completed?uid=user123

# Response
{
  "is_setup_completed": true,
  "auth_status": "completed"
}
```

---

### 6. POST `/webhook`
**Receive Voice Segments and Book Rides**

Main endpoint for receiving voice transcripts from Omi device.

**Request Body:**
```json
{
  "segments": [
    {
      "text": "book an uber",
      "speaker": "user"
    }
  ]
}
```

**Response:**
```json
{
  "message": "📝 Received 1 segment(s). Processing in 5s...",
  "booked": false,
  "batching": true
}
```

**Behavior:**
- Collects segments for 5 seconds of silence (sliding window)
- Each new segment restarts the 5-second countdown
- After 5 seconds of silence, processes all segments
- Validates user is authenticated
- Extracts locations using LLM
- Automatically books ride if valid locations detected

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| message | string | Status message |
| booked | boolean | Whether ride was booked |
| batching | boolean | Whether still collecting segments |

**Example - Single Segment:**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "text": "Book an Uber from SJSU to Cal Train Station",
        "speaker": "user"
      }
    ]
  }'

# Response (immediate)
{
  "message": "📝 Received 1 segment(s). Processing in 5s...",
  "booked": false,
  "batching": true
}

# After 5 seconds of silence:
# - Processes segment
# - Extracts: SJSU → Cal Train Station
# - Books ride
# - Captures screenshots
```

**Example - Multi-Segment (Sliding Window):**
```bash
# Segment 1 at t=0
curl -X POST http://localhost:8000/webhook \
  -d '{"segments": [{"text": "Book an Uber", "speaker": "user"}]}'

# Segment 2 at t=2 (timer restarts to t=7)
sleep 2
curl -X POST http://localhost:8000/webhook \
  -d '{"segments": [{"text": "from SJSU to Cal Train", "speaker": "user"}]}'

# Wait 5 seconds → processes at t=7
# Result: "Book an Uber from SJSU to Cal Train"
```

**Segment Format:**
```json
{
  "text": "string - the spoken text",
  "speaker": "string - speaker identifier (e.g., 'user', 'SPEAKER_0')"
}
```

**Processing Rules:**
1. ✅ Extracts actual location names (SJSU, Cal Train Station)
2. ✅ Corrects spelling (SJS → SJSU, Cal Trane → Cal Train)
3. ❌ Rejects generic terms (Current Location, Office, Home)
4. ✅ Requires both start and end locations
5. ✅ Validates user is authenticated
6. ✅ Captures screenshots at each step

---

### 7. GET `/health`
**Health Check**

Health check endpoint for deployment monitoring.

**Response:**
```json
{
  "status": "ok",
  "service": "omi-uber-app"
}
```

**Example:**
```bash
curl http://localhost:8000/health

# Response
{
  "status": "ok",
  "service": "omi-uber-app"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Missing required parameter: uid"
}
```

### 401 Unauthorized
```json
{
  "detail": "User not authenticated"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error processing request: [error message]"
}
```

---

## Rate Limiting

- **2FA attempts:** 3 per session
- **Bookings:** 1 per 30 seconds per user
- **Webhook:** No limit (non-blocking)

---

## Webhook Timing Examples

### Example 1: Quick Booking
```
t=0.0s: "Book an Uber to SJSU"
        → Waiting 5 seconds...

t=5.0s: 5 seconds of silence
        → Process and book
        → Captures 8 screenshots
        → Returns confirmation
```

### Example 2: Multi-Segment Booking
```
t=0.0s: "Book an Uber"
        → Waiting 5 seconds...

t=2.0s: "from SJSU"
        → Restart timer to t=7.0s

t=5.0s: "to Cal Train Station"
        → Restart timer to t=10.0s

t=10.0s: 5 seconds of silence
         → Join: "Book an Uber from SJSU to Cal Train Station"
         → Extract: SJSU → Cal Train Station
         → Book ride
```

### Example 3: Invalid Request
```
t=0.0s: "Book an Uber from my office"
        → Waiting 5 seconds...

t=5.0s: 5 seconds of silence
        → Process: "Book an Uber from my office"
        → LLM rejects (generic term: "my office")
        → No booking
        → Returns error
```

---

## Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Booking completed |
| 202 | Accepted | Segment received, processing |
| 400 | Bad Request | Missing parameters |
| 401 | Unauthorized | User not authenticated |
| 404 | Not Found | Invalid endpoint |
| 500 | Server Error | Processing failed |

---

## Data Storage

### User Files
```
users/
  └── {uid}.json
      {
        "uid": "user123",
        "uber_authenticated": true,
        "last_booking": "2025-10-25T11:00:00",
        "created_at": "2025-10-25T10:00:00"
      }
```

### Session Files
```
sessions/
  └── {uid}_uber_session.json
      {
        "cookies": [...],
        "origins": ["https://www.uber.com"],
        "localStorage": {...},
        "sessionStorage": {...}
      }
```

### Screenshots
```
snapshots/
  └── {uid}/
      ├── 01_pickup_filled.png
      ├── 02_pickup_selected.png
      ├── 03_dropoff_filled.png
      ├── 04_dropoff_selected.png
      ├── 05_ride_details.png
      ├── 06_ride_options.png
      ├── 07_ride_selected.png
      └── 08_booking_confirmation.png
```

---

## Common Workflows

### Workflow 1: First-Time User
```bash
# 1. Check if authenticated
curl http://localhost:8000/auth-status?uid=user123

# 2. If not authenticated, start auth
curl http://localhost:8000/auth?uid=user123
# (User completes authentication in browser)

# 3. Check setup completed
curl http://localhost:8000/setup-completed?uid=user123

# 4. Book a ride
curl -X POST http://localhost:8000/webhook \
  -d '{"segments": [{"text": "Book an Uber to SJSU", "speaker": "user"}]}'
```

### Workflow 2: Returning User
```bash
# 1. Book a ride directly
curl -X POST http://localhost:8000/webhook \
  -d '{"segments": [{"text": "Book an Uber to Cal Train", "speaker": "user"}]}'

# 2. Wait 5 seconds for processing
sleep 5

# 3. Check screenshots
ls snapshots/default_user/
```

### Workflow 3: Multi-Segment Booking
```bash
# 1. First segment
curl -X POST http://localhost:8000/webhook \
  -d '{"segments": [{"text": "Book an Uber", "speaker": "user"}]}'

# 2. Wait 2 seconds
sleep 2

# 3. Second segment (restarts timer)
curl -X POST http://localhost:8000/webhook \
  -d '{"segments": [{"text": "from SJSU to Cal Train", "speaker": "user"}]}'

# 4. Wait 5 seconds for processing
sleep 5

# 5. Ride is booked!
```

---

**API Version:** 1.0.0  
**Last Updated:** October 25, 2025
