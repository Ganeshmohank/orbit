#!/usr/bin/env python3
"""
Debug script to see live what's happening during booking.
Run this to see the browser in action with Playwright Inspector.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from uber_automation import uber_automation
from simple_storage import load_session

async def debug_booking():
    """Run booking with debug output."""
    uid = "default_user"
    start_location = "77 N almaden ave"
    end_location = "North park apartments"
    
    # Get auto_request from environment variable (default: False)
    auto_request = os.getenv("AUTO_REQUEST", "false").lower() == "true"
    
    print(f"\n🔍 Starting debug booking for {uid}")
    print(f"   From: {start_location}")
    print(f"   To: {end_location}")
    print(f"   Auto-request: {auto_request}\n")
    
    success, message, driver, eta = await uber_automation.book_ride(
        uid, start_location, end_location, auto_request=auto_request
    )
    
    print(f"\n✅ Result: {success}")
    print(f"📝 Message: {message}")
    print(f"🚗 Driver: {driver}")
    print(f"⏱️  ETA: {eta}\n")

if __name__ == "__main__":
    asyncio.run(debug_booking())
