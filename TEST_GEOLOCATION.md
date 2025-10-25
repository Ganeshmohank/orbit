# Testing Geolocation Feature

## Quick Test

### Test 1: Only Destination (Uses Geolocation)
```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "Book an Uber to Palace of Fine Arts", "speaker": "user"}]}'
```

**Expected Output:**
```
📝 Received 1 segment(s). Processing in 5s...
```

**Wait 5 seconds, then check logs:**
```
✅ LLM validation passed for default_user: None → Palace of Fine Arts
📍 Only destination provided, getting pickup from user's location...
📍 User location: San Francisco (37.7749, -122.4194)
🏛️ Nearest landmark: Ferry Building
✅ Got pickup location from IP: Ferry Building
🚗 Starting booking: Ferry Building → Palace of Fine Arts
```

### Test 2: Both Locations (No Geolocation)
```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "Book an Uber from Ferry Building to Palace of Fine Arts", "speaker": "user"}]}'
```

**Expected Output:**
```
✅ LLM validation passed for default_user: Ferry Building → Palace of Fine Arts
🚗 Starting booking: Ferry Building → Palace of Fine Arts
```

**Note:** No geolocation call (both locations provided)

### Test 3: Generic Pickup (Uses Geolocation)
```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "Book an Uber from my office to Palace of Fine Arts", "speaker": "user"}]}'
```

**Expected Output:**
```
✅ LLM validation passed for default_user: None → Palace of Fine Arts
📍 Only destination provided, getting pickup from user's location...
📍 User location: San Francisco (37.7749, -122.4194)
🏛️ Nearest landmark: Ferry Building
✅ Got pickup location from IP: Ferry Building
🚗 Starting booking: Ferry Building → Palace of Fine Arts
```

**Note:** LLM rejects "my office" (generic term), so geolocation is used

## Debug Logs

### Successful Geolocation
```
📍 User location: San Francisco (37.7749, -122.4194)
🏛️ Nearest landmark: Ferry Building
✅ Got pickup location from IP: Ferry Building
```

### Failed IP Geolocation
```
❌ Error getting user location: [error message]
⚠️ Could not get pickup location from IP
```

### Failed Reverse Geocoding
```
📍 User location: San Francisco (37.7749, -122.4194)
❌ Error getting landmark: [error message]
⚠️ Could not get pickup location from IP
```

## Testing Different Locations

### San Francisco
```bash
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber to Fishermans Wharf", "speaker": "user"}]}'
```

### New York
```bash
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber to Times Square", "speaker": "user"}]}'
```

### Los Angeles
```bash
curl -X POST "http://localhost:8000/webhook" \
  -d '{"segments": [{"text": "Book an Uber to Hollywood Sign", "speaker": "user"}]}'
```

## Expected Landmarks by City

| City | Typical Landmark |
|------|-----------------|
| San Francisco | Ferry Building, Alamo Square, Ferry Plaza |
| New York | Times Square, Central Park, Grand Central |
| Los Angeles | Hollywood Sign, Griffith Observatory, Getty Center |
| Chicago | Millennium Park, Navy Pier, Willis Tower |
| Seattle | Pike Place Market, Space Needle, Waterfront |

## Troubleshooting

### Issue: Geolocation not working
**Check:**
1. Internet connection (needs to reach ip-api.com and nominatim.openstreetmap.org)
2. Firewall/proxy blocking external requests
3. VPN enabled (may affect accuracy)

**Solution:**
```bash
# Test IP geolocation directly
curl http://ip-api.com/json/

# Test reverse geocoding
curl "https://nominatim.openstreetmap.org/reverse?format=json&lat=37.7749&lon=-122.4194"
```

### Issue: Wrong landmark detected
**Reason:** OpenStreetMap data may not have landmark for exact location

**Solution:**
- Provide explicit pickup location instead
- Use nearby well-known landmark name

### Issue: VPN affecting accuracy
**Reason:** IP geolocation returns VPN server location, not user location

**Solution:**
- Disable VPN for accurate location
- Or provide explicit pickup location

## Performance

### Timing
- IP Geolocation: ~200-500ms
- Reverse Geocoding: ~300-800ms
- Total: ~500-1300ms

### Impact on Booking
- Adds ~1-2 seconds to total booking time
- Still completes within 5-second silence window
- Negligible impact on user experience

## Feature Flags

### Disable Geolocation (if needed)
Edit `main.py` and comment out:
```python
# If only destination provided, get pickup from user's current location
# if not start_location and end_location:
#     start_location = await get_pickup_location_from_ip()
```

### Custom Geolocation Service
Edit `ride_detector.py` and replace `get_user_location_from_ip()` with your service:
```python
async def get_user_location_from_ip() -> Optional[Tuple[float, float]]:
    # Your custom implementation
    pass
```

## Privacy Testing

### What Data is Sent
1. User's IP address (to ip-api.com)
2. Coordinates (to nominatim.openstreetmap.org)

### What Data is NOT Sent
- ❌ User identity
- ❌ Exact home address
- ❌ Personal information
- ❌ Browsing history

### Verify Privacy
```bash
# Check what ip-api.com returns
curl http://ip-api.com/json/

# Check what nominatim returns
curl "https://nominatim.openstreetmap.org/reverse?format=json&lat=37.7749&lon=-122.4194"
```

---

**Test Date:** October 25, 2025  
**Feature Version:** 1.1.0  
**Status:** Ready for Testing
