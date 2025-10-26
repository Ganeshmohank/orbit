# Omi - Voice Entry Point

Omi is the hardware device that listens to conversations and sends voice commands to Orbit.

---

## What Omi Does

Omi is a wearable device that:
- Listens to your conversations continuously
- Transcribes voice to text
- Sends commands to Orbit's webhook
- Receives confirmations and status updates

---

## Omi's Role in Orbit

```
┌──────────────┐
│   You Speak  │
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│  Omi Device              │
│  - Records audio         │
│  - Transcribes to text   │
│  - Sends to Orbit        │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Orbit Webhook           │
│  POST /webhook           │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Nexus Processes         │
│  - Validates command     │
│  - Routes to service     │
│  - Executes action       │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Confirmation Back       │
│  - Status message        │
│  - Result details        │
└──────────────────────────┘
```

---

## Communication Protocol

### What Omi Sends

**Endpoint:** `POST /webhook`

**Data Format:**
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

**Fields:**
- `segments` - Array of voice segments (required)
  - `text` - Transcribed voice text
  - `speaker` - Who spoke (usually "user")
- `gps_lat` - Device GPS latitude (optional but helpful)
- `gps_lon` - Device GPS longitude (optional but helpful)

---

### What Omi Receives

**Response Format:**
```json
{
  "message": "Received 1 segment(s). Processing in 5s...",
  "booked": false,
  "batching": true
}
```

**Fields:**
- `message` - Human-readable status
- `booked` - Whether ride was booked
- `batching` - Whether system is collecting more segments

---

## Supported Commands

### Ride Booking
```
"Book an Uber to Pier 39"
"Get me a ride to the airport"
"Call an Uber from SJSU to downtown"
"Request an Uber to the train station"
```

### Jira Integration (Future)
```
"Update ticket PROJ-123 to done"
"Create a new bug ticket"
"Show me my assigned tasks"
```

### Calendar Integration (Future)
```
"Schedule a meeting tomorrow at 2pm"
"Add this to my calendar"
"Check my availability next week"
```

---

## How Omi Sends Multiple Segments

Omi doesn't send the entire command at once. It sends segments as you speak:

**Example Timeline:**

```
t=0s: Omi sends segment 1
      "Book an Uber"
      └─ Orbit receives and starts 5-second timer

t=2s: Omi sends segment 2
      "to Pier 39"
      └─ Orbit receives and restarts 5-second timer

t=7s: 5 seconds of silence detected
      └─ Orbit combines: "Book an Uber to Pier 39"
      └─ Processes and books ride
```

**Why segments?**
- Captures natural speech patterns
- Handles pauses and thinking time
- Allows Orbit to start processing when user finishes

---

## GPS Data

### Why GPS Matters

When you say "Book an Uber to Pier 39" without specifying pickup:
- Orbit needs to know where you are
- GPS provides accurate location
- System finds nearest landmark as pickup point

### GPS Priority

1. **Device GPS** (if provided) - Most accurate
2. **IP Geolocation** (fallback) - Less accurate
3. **Hardcoded Location** (last resort) - Default landmark

### Example with GPS

```
You say: "Book an Uber to Pier 39"
Omi sends GPS: (37.7749, -122.4194)

Orbit:
  1. Receives GPS coordinates
  2. Finds nearest landmark: "Ferry Building"
  3. Books: Ferry Building → Pier 39
```

---

## Omi Integration Points

### 1. Webhook Endpoint
- **URL:** `http://your-server/webhook`
- **Method:** POST
- **Content-Type:** application/json

### 2. Status Polling (Optional)
- **URL:** `http://your-server/auth-status?uid=user123`
- **Method:** GET
- **Purpose:** Check authentication status

### 3. Authentication (If Needed)
- **URL:** `http://your-server/auth?uid=user123`
- **Method:** GET
- **Purpose:** Start Uber authentication flow

---

## Setup Instructions

### 1. Configure Omi Device

Set the webhook URL in Omi settings:
```
Webhook URL: http://your-server.com/webhook
```

### 2. Enable GPS (Optional)

If your Omi device has GPS:
- Enable location services
- Omi will include GPS coordinates in webhook

### 3. Test Connection

Send a test command:
```
"Book an Uber to the airport"
```

Check Orbit logs for:
```
✅ Webhook received
📊 Payload: 1 segment(s)
```

---

## Troubleshooting

### Omi Not Connecting

**Check:**
1. Webhook URL is correct
2. Server is running and accessible
3. Network connectivity from Omi device

**Test:**
```bash
curl -X POST http://your-server/webhook \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "test", "speaker": "user"}]}'
```

### Commands Not Being Recognized

**Check:**
1. Speak clearly with specific location names
2. Avoid generic terms (My office, Home)
3. Check Orbit logs for LLM validation

### GPS Not Working

**Check:**
1. Device location services enabled
2. GPS coordinates included in webhook
3. Coordinates are valid (latitude -90 to 90, longitude -180 to 180)

---

## Best Practices

### 1. Speak Clearly
- Use specific location names
- Avoid mumbling or background noise
- Complete your thought before pausing

### 2. Use Real Locations
- ✅ "Book an Uber to Pier 39"
- ✅ "Get me a ride to SJSU"
- ❌ "Book an Uber to my office"
- ❌ "Get me a ride home"

### 3. Keep Segments Short
- Omi sends segments naturally
- Don't force long pauses
- Let Omi transcribe at its own pace

### 4. Enable GPS When Possible
- More accurate pickup location
- Better ride matching
- Faster booking

---

## Omi Device Specifications

### Requirements
- Internet connectivity (WiFi or cellular)
- GPS capability (optional)
- Microphone for voice capture

### Supported Platforms
- Omi wearable device
- Any device with microphone and internet

### Audio Format
- Automatically transcribed by Omi
- Sent as text to Orbit

---

## Future Enhancements

### 1. Real-Time Feedback
- Omi receives booking status in real-time
- Audio confirmation of actions

### 2. Context Awareness
- Omi remembers previous commands
- Understands pronouns ("Book another one")

### 3. Multi-Language Support
- Commands in different languages
- Automatic translation

### 4. Offline Mode
- Omi buffers commands when offline
- Syncs when connection restored

---

## Summary

Omi is the voice interface to Orbit:
- Listens and transcribes your voice
- Sends segments to Orbit webhook
- Receives confirmations
- Provides GPS coordinates for accuracy

Simple, clean, and focused on capturing your voice commands.

---

**Built with ❤️ for voice-activated productivity**
