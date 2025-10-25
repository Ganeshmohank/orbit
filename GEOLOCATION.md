# Geolocation & Landmark Detection

## Overview

When a user says "Book an Uber to Palace of Fine Arts" without specifying a pickup location, the system automatically:

1. **Gets user's IP address** → Determines approximate location
2. **Reverse geocodes** → Finds nearest landmark/address
3. **Uses landmark as pickup** → "Palace of Fine Arts" becomes destination
4. **Books ride** → From detected landmark to Palace of Fine Arts

## How It Works

### Example Flow

```
Omi Phone sends webhook: POST /webhook from IP 203.0.113.45
           ↓
System extracts phone's IP: 203.0.113.45
           ↓
User says: "Book an Uber to Palace of Fine Arts"
           ↓
LLM extracts: start=None, end="Palace of Fine Arts"
           ↓
System detects: start_location is missing
           ↓
Get location from phone's IP: 203.0.113.45
           ↓
Reverse geocode to find nearest landmark
           ↓
Result: start="Ferry Building" (or nearest landmark)
           ↓
Book: Ferry Building → Palace of Fine Arts
```

### Data Sources

#### 1. **IP Geolocation** - ip-api.com
- Free tier (no API key needed)
- Returns: latitude, longitude, city, country
- Accuracy: ~5-10km (city level)

#### 2. **Reverse Geocoding** - OpenStreetMap Nominatim
- Free, no API key needed
- Returns: nearest landmark, building, address
- Priority: landmark > building > neighbourhood > city

## Implementation

### Functions in `ride_detector.py`

#### `get_user_location_from_ip(ip_address)`
```python
async def get_user_location_from_ip(ip_address: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """
    Get user's approximate location from IP address.
    If ip_address is provided, uses that. Otherwise uses "me" (caller's IP).
    Returns (latitude, longitude) or None if failed.
    """
```

**Parameters:**
- `ip_address` - Optional IP address (e.g., from webhook request). If None, uses "me" endpoint.

**Returns:**
- `(37.7749, -122.4194)` - San Francisco coordinates
- `None` - If geolocation failed

**Example:**
```python
# Using phone's IP from webhook
lat, lon = await get_user_location_from_ip("203.0.113.45")
# Output: 📍 User location from IP 203.0.113.45: San Francisco (37.7749, -122.4194)

# Using caller's IP (default)
lat, lon = await get_user_location_from_ip()
# Output: 📍 User location from IP 203.0.113.45: San Francisco (37.7749, -122.4194)
```

#### `get_nearest_landmark(lat, lon)`
```python
async def get_nearest_landmark(lat: float, lon: float) -> Optional[str]:
    """
    Get nearest landmark/address to user's location.
    Returns landmark name or address.
    """
```

**Returns:**
- `"Ferry Building"` - Nearest landmark
- `"Downtown"` - If no landmark, returns neighbourhood
- `None` - If reverse geocoding failed

**Example:**
```python
landmark = await get_nearest_landmark(37.7749, -122.4194)
# Output: 🏛️ Nearest landmark: Ferry Building
```

#### `get_pickup_location_from_ip()`
```python
async def get_pickup_location_from_ip() -> Optional[str]:
    """
    Get user's current location and find nearest landmark.
    This becomes the pickup location.
    Returns landmark name or None if failed.
    """
```

**Returns:**
- `"Ferry Building"` - Nearest landmark to user
- `None` - If failed

**Example:**
```python
pickup = await get_pickup_location_from_ip()
# Output: 
# 📍 User location: San Francisco (37.7749, -122.4194)
# 🏛️ Nearest landmark: Ferry Building
```

## Integration in Webhook

### Before (v1.0.0)
```
User: "Book an Uber to Palace of Fine Arts"
LLM: start=None, end="Palace of Fine Arts"
Result: ❌ Missing start location → No booking
```

### After (v1.1.0)
```
User: "Book an Uber to Palace of Fine Arts"
LLM: start=None, end="Palace of Fine Arts"
Geolocation: start="Ferry Building" (from IP)
Result: ✅ Ferry Building → Palace of Fine Arts → Booked!
```

### Code in `main.py`

```python
# In _process_bucket_delayed()

# If only destination provided, get pickup from user's current location
if not start_location and end_location:
    logger.info(f"📍 Only destination provided, getting pickup from user's location...")
    start_location = await get_pickup_location_from_ip()
    if start_location:
        logger.info(f"✅ Got pickup location from IP: {start_location}")
    else:
        logger.warning(f"⚠️ Could not get pickup location from IP")
        return
```

## Supported Voice Commands

### With Explicit Pickup
```
"Book an Uber from Ferry Building to Palace of Fine Arts"
→ start="Ferry Building", end="Palace of Fine Arts"
→ Uses both locations as-is
```

### With Only Destination (Uses Geolocation)
```
"Book an Uber to Palace of Fine Arts"
→ start=None, end="Palace of Fine Arts"
→ Gets start from IP geolocation
→ Result: start="Ferry Building", end="Palace of Fine Arts"
```

### With Generic Pickup (Uses Geolocation)
```
"Book an Uber from my office to Palace of Fine Arts"
→ LLM rejects "my office" (generic term)
→ start=None, end="Palace of Fine Arts"
→ Gets start from IP geolocation
→ Result: start="Ferry Building", end="Palace of Fine Arts"
```

## Accuracy & Limitations

### Accuracy
- **IP Geolocation:** ~5-10km (city level)
  - Accurate for cities
  - Less accurate for rural areas
  - VPN/Proxy may affect accuracy

- **Reverse Geocoding:** ~100m (street level)
  - Finds nearest landmark
  - Works well in urban areas
  - May return neighbourhood if no landmark nearby

### Limitations
- ❌ Not precise for exact addresses
- ❌ May not work in remote areas
- ❌ VPN/Proxy affects accuracy
- ❌ Requires internet connection
- ✅ Works for general "pick me up near here" use cases

## Example Scenarios

### Scenario 1: User at Home
```
User IP: 37.7749, -122.4194 (San Francisco)
Nearest Landmark: "Alamo Square"
User says: "Book an Uber to Airport"
Result: Alamo Square → Airport
```

### Scenario 2: User at Work
```
User IP: 37.3382, -121.8863 (San Jose)
Nearest Landmark: "San Jose Convention Center"
User says: "Book an Uber to SJSU"
Result: San Jose Convention Center → SJSU
```

### Scenario 3: User at Coffee Shop
```
User IP: 37.7749, -122.4194 (San Francisco)
Nearest Landmark: "Blue Bottle Coffee"
User says: "Book an Uber to Ferry Building"
Result: Blue Bottle Coffee → Ferry Building
```

## Privacy Considerations

### Data Collected
- User's IP address (to determine location)
- Approximate coordinates (5-10km accuracy)
- Nearest landmark name

### Data NOT Collected
- ❌ Exact home address
- ❌ Precise GPS coordinates
- ❌ User identity
- ❌ Browsing history

### Privacy Notes
- IP geolocation is approximate (city level)
- No personal data stored
- No tracking or profiling
- Complies with privacy regulations

## Configuration

### Enable/Disable
Currently always enabled when only destination is provided.

To disable, remove this code from `main.py`:
```python
# If only destination provided, get pickup from user's current location
if not start_location and end_location:
    start_location = await get_pickup_location_from_ip()
```

### Custom Geolocation Service
To use a different geolocation service, modify `get_user_location_from_ip()`:

```python
# Example: Using MaxMind GeoIP2
async def get_user_location_from_ip() -> Optional[Tuple[float, float]]:
    reader = geoip2.database.Reader('GeoLite2-City.mmdb')
    response = reader.city(ip_address)
    return response.location.latitude, response.location.longitude
```

## Testing

### Manual Test
```bash
# Say only destination
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "Book an Uber to Palace of Fine Arts", "speaker": "user"}]}'

# Wait 5 seconds
# Check logs for:
# 📍 User location: San Francisco (37.7749, -122.4194)
# 🏛️ Nearest landmark: Ferry Building
# ✅ Got pickup location from IP: Ferry Building
# 🚗 Starting booking: Ferry Building → Palace of Fine Arts
```

### Debug Logs
```
📍 User location: San Francisco (37.7749, -122.4194)
🏛️ Nearest landmark: Ferry Building
✅ Got pickup location from IP: Ferry Building
🚗 Starting booking: Ferry Building → Palace of Fine Arts
```

## Future Improvements

- [ ] Allow user to override detected location
- [ ] Cache landmark results (5 minutes)
- [ ] Support multiple landmarks (let user choose)
- [ ] Integrate with device GPS (if available)
- [ ] Support for saved locations (Home, Work, etc.)
- [ ] Fallback to city name if no landmark found

---

**Version:** 1.1.0 (New Feature)  
**Status:** Implemented  
**Dependencies:** httpx, OpenStreetMap Nominatim
