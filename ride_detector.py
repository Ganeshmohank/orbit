import re
from typing import Optional, List
from openai import OpenAI

client = OpenAI()


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
