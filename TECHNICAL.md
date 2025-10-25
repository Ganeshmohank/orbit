# Technical Documentation - Omi Uber App

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Omi Device (Voice Input)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /webhook                                       │  │
│  │  - Receives voice segments                           │  │
│  │  - Sliding window collection (5s silence)            │  │
│  │  - Validates user authentication                     │  │
│  │  - Triggers booking automation                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    ┌────────┐      ┌─────────┐      ┌──────────┐
    │  LLM   │      │ Browser │      │ Storage  │
    │OpenAI  │      │Playwright│     │ JSON     │
    └────────┘      └─────────┘      └──────────┘
        │                ▼
        │           ┌──────────────┐
        │           │ Uber Website │
        │           └──────────────┘
        │                ▼
        └──────────────────────────────────────────────────────►
                    (Booking Confirmation)
```

## Core Components

### 1. Webhook Handler (`main.py`)

**Endpoint:** `POST /webhook`

**Segment Collection Flow:**
```python
# Global state
segment_buckets = {}              # {uid: [segments]}
segment_last_arrival = {}         # {uid: timestamp}
bucket_timers = {}                # {uid: asyncio.Task}
BUCKET_WAIT_TIME = 5              # seconds

# When segment arrives:
1. If uid not in segment_buckets:
   - Create bucket
   - Start monitoring task
   
2. Add segments to bucket
3. Update segment_last_arrival[uid] = time.time()
4. Return immediately (non-blocking)

# Monitoring task (runs continuously):
while True:
    await asyncio.sleep(0.5)
    if uid not in segment_buckets:
        return  # Already processed
    
    time_since_last = time.time() - segment_last_arrival[uid]
    if time_since_last >= 5:
        # Process bucket
        break
```

**Key Features:**
- ✅ Sliding window: Each new segment resets the countdown
- ✅ Non-blocking: Returns immediately to caller
- ✅ Concurrent: Multiple users can have concurrent buckets
- ✅ Efficient: Checks every 500ms, not continuously

### 2. Destination Extraction (`ride_detector.py`)

**Function:** `extract_destinations(text: str)`

**LLM Prompt:**
```
Extract the start location and end location from this voice command.
IMPORTANT RULES:
1. Return ONLY actual location names (e.g., "SJSU", "Cal Train Station")
2. NEVER return "Current Location", "Office", "Home", etc.
3. Ignore spelling mistakes but keep location name (e.g., "SJS" → "SJSU")
4. Return format: START_LOCATION|END_LOCATION
5. If only one location: return "NOT_FOUND|END_LOCATION"
6. If no valid locations: return "NOT_FOUND|NOT_FOUND"
```

**Validation:**
```python
# After LLM response
if "NOT_FOUND" in result:
    return None, None

# Check for generic terms
generic_terms = ["current location", "office", "home", "my place", "work"]
if start.lower() in generic_terms or end.lower() in generic_terms:
    return None, None

return start, end
```

### 3. Browser Automation (`uber_automation.py`)

**Flow:**
```
1. Load session (cookies + localStorage)
2. Navigate to uber.com
3. Fill pickup location
4. Select pickup suggestion
5. Fill dropoff location
6. Select dropoff suggestion
7. Click "See prices"
8. Select ride option
9. Click "Request"
10. Capture screenshot
```

**Screenshot Capture:**
```python
async def _capture_screenshot(page, uid: str, step_name: str):
    user_snapshots_dir = f"snapshots/{uid}"
    os.makedirs(user_snapshots_dir, exist_ok=True)
    
    screenshot_path = f"{user_snapshots_dir}/{step_name}.png"
    await page.screenshot(path=screenshot_path)
    return screenshot_path
```

**Steps Captured:**
- 01_pickup_filled
- 02_pickup_selected
- 03_dropoff_filled
- 04_dropoff_selected
- 05_ride_details
- 06_ride_options
- 07_ride_selected
- 08_booking_confirmation

### 4. Session Management (`simple_storage.py`)

**Storage Structure:**
```
users/
  └── default_user.json
      {
        "uid": "default_user",
        "uber_authenticated": true,
        "last_booking": "2025-10-25T11:00:00",
        "created_at": "2025-10-25T10:00:00"
      }

sessions/
  └── default_user_uber_session.json
      {
        "cookies": [...],
        "origins": ["https://www.uber.com"],
        "localStorage": {...},
        "sessionStorage": {...}
      }
```

## Data Flow

### Booking Request Flow

```
1. Voice Input (Omi Device)
   ↓
2. POST /webhook
   ├─ Receive segments
   ├─ Add to bucket
   ├─ Update last_arrival
   └─ Return immediately
   ↓
3. Monitoring Task (Background)
   ├─ Check every 500ms
   ├─ Wait for 5s silence
   └─ Trigger processing
   ↓
4. Process Bucket
   ├─ Join segments
   ├─ Send to LLM
   ├─ Extract locations
   └─ Validate user
   ↓
5. Browser Automation
   ├─ Load session
   ├─ Navigate to Uber
   ├─ Fill locations
   ├─ Select ride
   ├─ Click request
   └─ Capture screenshots
   ↓
6. Confirmation
   ├─ Return success
   └─ Store booking record
```

## Timing Behavior

### Example: Multi-Segment Booking

```
Timeline:
t=0.0s: Segment 1 arrives ("Book an Uber")
        → bucket = ["Book an Uber"]
        → last_arrival = 0.0
        → waiting until t=5.0

t=2.3s: Segment 2 arrives ("from SJSU")
        → bucket = ["Book an Uber", "from SJSU"]
        → last_arrival = 2.3
        → waiting until t=7.3

t=5.1s: Segment 3 arrives ("to Cal Train")
        → bucket = ["Book an Uber", "from SJSU", "to Cal Train"]
        → last_arrival = 5.1
        → waiting until t=10.1

t=10.1s: 5 seconds of silence detected
         → Process: "Book an Uber from SJSU to Cal Train"
         → Extract: SJSU → Cal Train
         → Book ride
```

## Error Handling

### Authentication Check
```python
user_data = load_user_data(uid)
if not user_data.get("uber_authenticated"):
    logger.warning(f"⚠️ User {uid} not authenticated")
    return  # Skip booking
```

### Login Button Detection
```python
if "login button" in message.lower():
    logger.warning(f"⚠️ FOUND LOGIN BUTTON - User may not be authenticated!")
    logger.warning(f"⚠️ Please visit: http://localhost:8000/auth?uid={uid}")
```

### Rate Limiting
```python
MIN_BOOKING_INTERVAL = 30  # seconds

if uid in last_booking_time:
    time_since_last = current_time - last_booking_time[uid]
    if time_since_last < MIN_BOOKING_INTERVAL:
        logger.info(f"⏱️ Rate limited for {uid}")
        return
```

## Performance Considerations

### Memory Usage
- **Segment buckets:** O(n) where n = number of active users
- **Each bucket:** ~1KB per 100 segments
- **Typical:** <10MB for 1000 concurrent users

### Latency
- **Segment arrival to response:** <10ms
- **Monitoring check interval:** 500ms
- **Processing delay:** 5-10 seconds (5s wait + processing)
- **Browser automation:** 30-60 seconds

### Concurrency
- **Async/await:** Handles thousands of concurrent requests
- **Browser pool:** Reuses browsers per user
- **Non-blocking:** Webhook returns immediately

## Testing

### Manual Testing
```bash
# Test 1: Single segment
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "Book an Uber to SJSU", "speaker": "user"}]}'

# Test 2: Multi-segment (sliding window)
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber", "speaker": "user"}]}'
sleep 2
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "to Cal Train", "speaker": "user"}]}'
sleep 5
# Should process both segments together
```

### Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check bucket state
print(segment_buckets)
print(segment_last_arrival)
print(bucket_timers)
```

## Future Improvements

- [ ] Database instead of JSON files
- [ ] WebSocket for real-time updates
- [ ] Multi-language support
- [ ] Ride history and analytics
- [ ] User preferences (UberX, UberPool, etc.)
- [ ] Estimated price display
- [ ] Driver rating display
- [ ] Cancellation support

## Security Notes

- ✅ No credentials stored in code
- ✅ Session files not in version control
- ✅ API keys in environment variables
- ✅ HTTPS enforced in production
- ⚠️ Headless browser may trigger Uber security
- ⚠️ Session persistence depends on Uber's policies

---

**Last Updated:** October 25, 2025
**Version:** 1.0.0
