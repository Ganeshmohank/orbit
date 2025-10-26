import re
import httpx
from typing import Optional, List, Tuple
from openai import OpenAI

client = OpenAI()

# ============================================================================
# Geolocation and Landmark Detection
# ============================================================================

async def get_user_location_from_ip(ip_address: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """
    Get user's approximate location from IP address.
    If ip_address is provided, uses that. Otherwise uses current request IP.
    Returns (latitude, longitude) or None if failed.
    """
    try:
        # Use provided IP or get current IP
        target_ip = ip_address or "me"
        
        async with httpx.AsyncClient(timeout=5.0) as client_http:
            # Using ip-api.com (free tier, no API key needed)
            # "me" endpoint returns caller's IP, or specify custom IP
            response = await client_http.get(f"http://ip-api.com/json/{target_ip}")
            data = response.json()
            
            if data.get("status") == "success":
                lat = data.get("lat")
                lon = data.get("lon")
                city = data.get("city", "Unknown")
                returned_ip = data.get("query", "unknown")
                print(f"📍 User location from IP {returned_ip}: {city} ({lat}, {lon})")
                return lat, lon
            else:
                print(f"⚠️ Could not get location: {data.get('message')}")
                return None
    except Exception as e:
        print(f"❌ Error getting user location: {e}")
        return None


async def get_nearest_landmark(lat: float, lon: float) -> Optional[str]:
    """
    Get nearest landmark/address to user's location.
    Uses hardcoded fallback for San Francisco coordinates.
    """
    # Hardcoded landmarks for known coordinates
    LANDMARK_FALLBACKS = {
        (37.7749, -122.4194): "San Pedro Square",  # San Francisco downtown
        (37.802087, -122.448663): "77 N alamden ave",  # Palace of Fine Arts
    }
    
    # Check if coordinates match known locations (with small tolerance)
    for (known_lat, known_lon), landmark in LANDMARK_FALLBACKS.items():
        lat_diff = abs(lat - known_lat)
        lon_diff = abs(lon - known_lon)
        if lat_diff < 0.01 and lon_diff < 0.01:  # ~1km tolerance
            print(f"🏛️ Nearest landmark: {landmark}")
            return landmark
    
    # Default fallback to Palace of Fine Arts
    print(f"🏛️ Using default landmark: 77 N alamden ave")
    return "77 N alamden ave"


async def get_pickup_location_from_ip(ip_address: Optional[str] = None, gps_lat: Optional[float] = None, gps_lon: Optional[float] = None) -> Optional[str]:
    """
    Get user's current location and find nearest landmark.
    This becomes the pickup location.
    
    Args:
        ip_address: Optional IP address from webhook request.
                   If not provided, uses "me" (caller's IP).
        gps_lat: Optional GPS latitude from device (preferred over IP geolocation)
        gps_lon: Optional GPS longitude from device (preferred over IP geolocation)
    
    Returns landmark name or None if failed.
    """
    # Prefer GPS coordinates if provided
    if gps_lat is not None and gps_lon is not None:
        print(f"📍 Using device GPS: ({gps_lat}, {gps_lon})")
        lat, lon = gps_lat, gps_lon
    else:
        # Fallback: Use Palace of Fine Arts coordinates (hardcoded)
        print(f"📍 No GPS provided, using Palace of Fine Arts fallback coordinates")
        lat, lon = 37.802087, -122.448663
    
    # Get nearest landmark
    landmark = await get_nearest_landmark(lat, lon)
    return landmark


async def validate_and_extract_ride_request(text: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Single LLM call to:
    1. Validate if this is a ride booking request
    2. Extract start and end locations (if valid ride request)
    
    Returns (is_ride_request, start_location, end_location)
    """
    try:
        prompt = f"""Analyze this user text and determine:
1. Is the user asking to book a ride (Uber, Lyft, taxi, etc.)?
2. If YES, extract the start and end locations

IMPORTANT RULES:
- Return ONLY actual location names (e.g., "SJSU", "Cal Train Station", "Downtown")
- NEVER return "Current Location", "Office", "Home", or similar generic terms
- Ignore spelling mistakes but keep location names as spoken
- If only one location mentioned, start is "NOT_FOUND"
- If not a ride request, return "NO|NOT_FOUND|NOT_FOUND"

User text: "{text}"

Respond with ONLY: YES|START_LOCATION|END_LOCATION or NO|NOT_FOUND|NOT_FOUND"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100,
        )

        result = response.choices[0].message.content.strip()
        print(f"🤖 LLM validation & extraction: {result}")
        
        parts = result.split("|")
        if len(parts) != 3:
            print(f"⚠️ Unexpected LLM response format: {result}")
            return False, None, None
        
        is_ride = parts[0].strip().upper() == "YES"
        start = parts[1].strip() if parts[1].strip() != "NOT_FOUND" else None
        end = parts[2].strip() if parts[2].strip() != "NOT_FOUND" else None
        
        if not is_ride:
            print(f"❌ Not a ride booking request")
            return False, None, None
        
        print(f"✅ Ride request detected: {start} → {end}")
        return True, start, end

    except Exception as e:
        print(f"Error in LLM validation: {e}")
        return False, None, None


async def detect_trigger_and_destinations(segments: List) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Single LLM call to detect if user is requesting a ride and extract locations.
    Uses LLM for flexible detection - no strict patterns.
    Returns (is_ride_request, start_location, end_location)
    """
    # Handle both dict and Pydantic model segments
    combined_text = " ".join([
        seg.get("text", "") if isinstance(seg, dict) else seg.text 
        for seg in segments
    ])

    print(f"📝 Processing segments: '{combined_text}'")
    
    # Single LLM call: validate ride request AND extract locations
    is_ride, start_location, end_location = await validate_and_extract_ride_request(combined_text)
    
    return is_ride, start_location, end_location
