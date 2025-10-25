# GPS Workaround - Accurate Location Detection

## Problem

IP geolocation can be inaccurate due to:
- VPN/Proxy usage
- ISP routing through different regions
- Outdated IP geolocation databases
- Corporate/home network configurations

**Example:**
```
User is in: San Francisco
IP geolocation shows: Council Bluffs, Iowa ❌
```

## Solution: Send GPS Coordinates

Include GPS coordinates in the webhook request for accurate location detection.

### Webhook Format with GPS

```json
{
  "segments": [
    {"text": "Book an Uber to SJSU", "speaker": "user"}
  ],
  "gps_lat": 37.7749,
  "gps_lon": -122.4194
}
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {"text": "Book an Uber to Palace of Fine Arts", "speaker": "user"}
    ],
    "gps_lat": 37.7749,
    "gps_lon": -122.4194
  }'
```

### Expected Output

**With GPS (Accurate):**
```
📍 GPS coordinates provided: (37.7749, -122.4194)
📍 Using GPS coordinates: (37.7749, -122.4194)
🔍 Reverse geocoding coordinates: (37.7749, -122.4194)
📍 Full address data:
   - landmark: Ferry Building
   - building: N/A
   - neighbourhood: Financial District
   - city: San Francisco
✅ Selected landmark: Ferry Building
🏛️ Nearest landmark: Ferry Building
✅ Got pickup location: Ferry Building
🎯 Final booking route: Ferry Building → Palace of Fine Arts
```

**Without GPS (May be inaccurate):**
```
📱 Using phone IP for geolocation: 2600:1900:0:2d04::500
🔍 Reverse geocoding coordinates: (41.2619, -95.8608)
📍 Full address data:
   - landmark: N/A
   - building: N/A
   - city: Council Bluffs
✅ Selected landmark: Council Bluffs
🏛️ Nearest landmark: Council Bluffs
✅ Got pickup location: Council Bluffs
🎯 Final booking route: Council Bluffs → SJSU ❌
```

## How to Get GPS Coordinates

### Option 1: Omi Device GPS
If Omi has GPS capability, extract coordinates from device:

```python
# In Omi app/device code
import location

lat, lon = location.get_current_location()
# Send to webhook with gps_lat and gps_lon
```

### Option 2: Manual Testing
Use any GPS coordinate service:

**San Francisco:**
```
gps_lat: 37.7749
gps_lon: -122.4194
```

**New York:**
```
gps_lat: 40.7128
gps_lon: -74.0060
```

**Los Angeles:**
```
gps_lat: 34.0522
gps_lon: -118.2437
```

### Option 3: Browser Geolocation API
If webhook comes from web browser:

```javascript
navigator.geolocation.getCurrentPosition(function(position) {
  const lat = position.coords.latitude;
  const lon = position.coords.longitude;
  
  // Send to webhook
  fetch('/webhook', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      segments: [{text: "Book an Uber to SJSU", speaker: "user"}],
      gps_lat: lat,
      gps_lon: lon
    })
  });
});
```

## Priority Order

The system uses this priority:

```
1. GPS coordinates (if provided in webhook)
   ↓
2. IP geolocation (fallback)
```

**Logic:**
```python
if gps_lat and gps_lon:
    # Use GPS (most accurate)
    location = (gps_lat, gps_lon)
else:
    # Fall back to IP geolocation
    location = await get_user_location_from_ip(phone_ip)
```

## Logging

### GPS Used
```
📍 GPS coordinates provided: (37.7749, -122.4194)
📍 Using GPS coordinates: (37.7749, -122.4194)
```

### IP Fallback
```
📱 Using phone IP for geolocation: 203.0.113.45
```

## Implementation Details

### Webhook Body Parser
```python
# In main.py webhook endpoint
gps_lat = body.get("gps_lat")
gps_lon = body.get("gps_lon")
if gps_lat and gps_lon:
    logger.info(f"📍 GPS coordinates provided: ({gps_lat}, {gps_lon})")
```

### Geolocation Function
```python
# In ride_detector.py
async def get_pickup_location_from_ip(
    ip_address: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None
) -> Optional[str]:
    # Prefer GPS coordinates if provided
    if gps_lat is not None and gps_lon is not None:
        print(f"📍 Using device GPS: ({gps_lat}, {gps_lon})")
        lat, lon = gps_lat, gps_lon
    else:
        # Fall back to IP geolocation
        location = await get_user_location_from_ip(ip_address)
        if not location:
            return None
        lat, lon = location
    
    # Get nearest landmark
    landmark = await get_nearest_landmark(lat, lon)
    return landmark
```

## Testing

### Test 1: With GPS (Accurate)
```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [{"text": "Book an Uber to SJSU", "speaker": "user"}],
    "gps_lat": 37.3382,
    "gps_lon": -121.8863
  }'

# Expected: SJSU area landmark
```

### Test 2: Without GPS (May be inaccurate)
```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [{"text": "Book an Uber to SJSU", "speaker": "user"}]
  }'

# May show wrong location if IP geolocation is inaccurate
```

### Test 3: Different Locations
```bash
# San Francisco
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber to Ferry Building", "speaker": "user"}], "gps_lat": 37.7749, "gps_lon": -122.4194}'

# New York
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber to Times Square", "speaker": "user"}], "gps_lat": 40.7580, "gps_lon": -73.9855}'

# Los Angeles
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber to Hollywood Sign", "speaker": "user"}], "gps_lat": 34.1381, "gps_lon": -118.3215}'
```

## Omi Integration

### For Omi App Developers

If integrating with Omi device, include GPS in webhook:

```python
# In Omi app code
import requests
import location

# Get current location
lat, lon = location.get_current_location()

# Send webhook with GPS
response = requests.post(
    "https://your-app.railway.app/webhook",
    json={
        "segments": [{"text": user_speech, "speaker": "user"}],
        "gps_lat": lat,
        "gps_lon": lon
    }
)
```

### Webhook URL Configuration

In Omi app settings:
```
Webhook URL: https://your-app.railway.app/webhook
```

The webhook will automatically use GPS if provided.

## Accuracy Comparison

| Method | Accuracy | Latency | Reliability |
|--------|----------|---------|-------------|
| GPS | ~5-10m | ~100-500ms | High (if available) |
| IP Geolocation | ~5-10km | ~200-500ms | Medium (depends on ISP) |
| Reverse Geocoding | ~100m | ~300-800ms | High |

## Fallback Chain

```
1. GPS provided in webhook
   ↓ (if not available)
2. IP geolocation
   ↓ (if both fail)
3. Skip booking, ask user for explicit pickup location
```

## Privacy

- GPS coordinates are only used for landmark detection
- No tracking or storage of location history
- Coordinates are not sent to external services (only used locally)
- Complies with privacy regulations

---

**Version:** 1.1.0  
**Status:** Implemented  
**Recommended:** Use GPS for accurate location detection
