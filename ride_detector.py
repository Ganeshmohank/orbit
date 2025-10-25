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
        (37.7749, -122.4194): "Ferry Building",  # San Francisco downtown
        (37.802087, -122.448663): "Palace of Fine Arts",  # Palace of Fine Arts
    }
    
    # Check if coordinates match known locations (with small tolerance)
    for (known_lat, known_lon), landmark in LANDMARK_FALLBACKS.items():
        lat_diff = abs(lat - known_lat)
        lon_diff = abs(lon - known_lon)
        if lat_diff < 0.01 and lon_diff < 0.01:  # ~1km tolerance
            print(f"🏛️ Nearest landmark: {landmark}")
            return landmark
    
    # Default fallback to Palace of Fine Arts
    print(f"🏛️ Using default landmark: Palace of Fine Arts")
    return "Palace of Fine Arts"


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


def is_trigger_phrase(text: str) -> bool:
    """Check if text contains Uber booking trigger phrases."""
    patterns = [
        r"book\s+(?:me\s+)?(?:an?\s+)?uber",
        r"get\s+(?:me\s+)?(?:an?\s+)?(?:uber\s+)?ride",
        r"call\s+(?:me\s+)?(?:an?\s+)?uber",
        r"request\s+(?:an?\s+)?uber",
        r"order\s+(?:an?\s+)?uber",
        r"uber\s+(?:ride|from)",
    ]

    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def extract_destinations(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract start and end locations from voice text using OpenAI."""
    try:
        prompt = f"""Extract the start location and end location from this voice command.
IMPORTANT RULES:
1. Return ONLY actual location names (e.g., "SJSU", "Cal Train Station", "Downtown")
2. NEVER return "Current Location", "Office", "Home", or similar generic terms
3. Ignore spelling mistakes but keep the location name as spoken (e.g., "SJS" → "SJSU", "Cal Trane" → "Cal Train")
4. Return format: START_LOCATION|END_LOCATION
5. If only one location is mentioned, return "NOT_FOUND|END_LOCATION"
6. If no valid locations are mentioned, return "NOT_FOUND|NOT_FOUND"

Voice command: "{text}"

Locations:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100,
        )

        result = response.choices[0].message.content.strip()

        if "NOT_FOUND" in result.upper():
            parts = result.split("|")
            if len(parts) == 2:
                start = parts[0].strip()
                end = parts[1].strip()
                if start == "NOT_FOUND" and end != "NOT_FOUND":
                    return None, end
                if end == "NOT_FOUND":
                    return None, None
            return None, None

        parts = result.split("|")
        if len(parts) == 2:
            start = parts[0].strip()
            end = parts[1].strip()
            
            # Validate that we have actual location names, not generic terms
            generic_terms = ["current location", "office", "home", "my place", "work"]
            if start.lower() in generic_terms or end.lower() in generic_terms:
                return None, None
            
            if start and end:
                return start, end

        return None, None

    except Exception as e:
        print(f"Error extracting destinations: {e}")
        return None, None


def detect_trigger_and_destinations(segments: List) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Detect trigger phrase and extract start/end locations from segments.
    Returns (is_trigger, start_location, end_location)
    """
    # Handle both dict and Pydantic model segments
    combined_text = " ".join([
        seg.get("text", "") if isinstance(seg, dict) else seg.text 
        for seg in segments
    ])

    if not is_trigger_phrase(combined_text):
        return False, None, None

    start_location, end_location = extract_destinations(combined_text)
    return True, start_location, end_location
