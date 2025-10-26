import os
import asyncio
import time
import json
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging

# Load environment variables FIRST before importing modules that use them
load_dotenv()

from auth_manager import auth_manager, active_browsers
from uber_automation import uber_automation
from ride_detector import detect_trigger_and_destinations, get_pickup_location_from_ip
from simple_storage import (
    load_user_data,
    update_user_status,
    load_session,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Omi Uber App", version="1.0.0")

# Rate limiting to prevent bombarding Uber
last_booking_time = {}
MIN_BOOKING_INTERVAL = 30  # Minimum 15 seconds between bookings per user

# Active bookings - only 1 per user
active_bookings = {}  # {uid: bool}

# Segment buckets for collecting voice data
segment_buckets = {}  # {uid: [segments]}
segment_last_arrival = {}  # {uid: timestamp of last segment}
bucket_timers = {}  # {uid: asyncio.Task}
BUCKET_WAIT_TIME = 5  # Wait 5 seconds from last segment before processing

# Models
class VoiceSegment(BaseModel):
    text: str
    speaker: str


class WebhookRequest(BaseModel):
    uid: str
    segments: list[VoiceSegment]


class TwoFARequest(BaseModel):
    uid: str
    code: str


class AuthStatusResponse(BaseModel):
    status: str
    message: str


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment."""
    return {"status": "ok", "service": "omi-uber-app"}


# ============================================================================
# HOME PAGE
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def home(uid: Optional[str] = None):
    """App home page - shows authentication status and usage instructions."""
    if not uid:
        uid = "default_user"

    user_data = load_user_data(uid)
    is_authenticated = user_data.get("uber_authenticated", False)
    auth_status = user_data.get("auth_status", "not_authenticated")

    if auth_status == "waiting_2fa":
        status_html = """
        <div class="status-box waiting">
            <div class="spinner"></div>
            <h2>📱 Waiting for 2FA Verification</h2>
            <p>Please enter your verification code below</p>
        </div>
        """
    elif is_authenticated:
        status_html = """
        <div class="status-box success">
            <h2>✅ Uber Connected</h2>
            <p>Your Uber account is authenticated and ready to use.</p>
            <div class="instructions">
                <h3>How to use:</h3>
                <ul>
                    <li>Say "Book an Uber to [destination]"</li>
                    <li>Or "Get me a ride to [destination]"</li>
                    <li>Your ride will be booked automatically</li>
                </ul>
            </div>
            <a href="/auth" class="btn btn-secondary">Re-authenticate</a>
        </div>
        """
    else:
        status_html = """
        <div class="status-box pending">
            <h2>🔐 Connect Your Uber Account</h2>
            <p>Authenticate once to start booking rides with your voice.</p>
            <a href="/auth" class="btn btn-primary">Connect Uber Account</a>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Omi Uber App</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}

            .container {{
                width: 100%;
                max-width: 500px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 40px;
                text-align: center;
            }}

            .header {{
                margin-bottom: 30px;
            }}

            .logo {{
                font-size: 48px;
                margin-bottom: 10px;
            }}

            .header h1 {{
                font-size: 28px;
                color: #333;
                margin-bottom: 5px;
            }}

            .header p {{
                color: #666;
                font-size: 14px;
            }}

            .status-box {{
                margin: 30px 0;
                padding: 25px;
                border-radius: 15px;
                background: #f8f9fa;
            }}

            .status-box.success {{
                background: #d4edda;
                border: 2px solid #28a745;
            }}

            .status-box.success h2 {{
                color: #155724;
            }}

            .status-box.pending {{
                background: #fff3cd;
                border: 2px solid #ffc107;
            }}

            .status-box.pending h2 {{
                color: #856404;
            }}

            .status-box.waiting {{
                background: #cfe2ff;
                border: 2px solid #0d6efd;
            }}

            .status-box.waiting h2 {{
                color: #084298;
            }}

            .status-box h2 {{
                font-size: 22px;
                margin-bottom: 10px;
            }}

            .status-box p {{
                color: #666;
                font-size: 14px;
                margin-bottom: 15px;
            }}

            .instructions {{
                text-align: left;
                background: white;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
            }}

            .instructions h3 {{
                font-size: 14px;
                color: #333;
                margin-bottom: 10px;
            }}

            .instructions ul {{
                list-style: none;
                padding-left: 0;
            }}

            .instructions li {{
                padding: 8px 0;
                color: #666;
                font-size: 13px;
                border-bottom: 1px solid #eee;
            }}

            .instructions li:last-child {{
                border-bottom: none;
            }}

            .btn {{
                display: inline-block;
                padding: 12px 30px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                margin-top: 15px;
            }}

            .btn-primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}

            .btn-primary:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }}

            .btn-secondary {{
                background: #6c757d;
                color: white;
                font-size: 12px;
                padding: 8px 20px;
            }}

            .btn-secondary:hover {{
                background: #5a6268;
            }}

            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #0d6efd;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }}

            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}

            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 12px;
            }}

            @media (max-width: 480px) {{
                .container {{
                    padding: 25px;
                }}

                .header h1 {{
                    font-size: 24px;
                }}

                .status-box h2 {{
                    font-size: 18px;
                }}

                .btn {{
                    width: 100%;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚗</div>
                <h1>Omi Uber</h1>
                <p>Voice-Activated Ride Booking</p>
            </div>

            {status_html}

            <div class="footer">
                <p>Secure authentication • One-time setup • Voice-activated bookings</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


@app.get("/auth")
async def auth_page(uid: Optional[str] = None):
    """Launch authentication flow."""
    if not uid:
        uid = "default_user"

    try:
        # Start login flow in background
        asyncio.create_task(auth_manager.start_login_flow(uid))

        # Return HTML with real-time status updates
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Authenticating...</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}

                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 500px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    text-align: center;
                }}

                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }}

                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}

                h2 {{
                    color: #333;
                    margin-bottom: 10px;
                }}

                #status {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 20px;
                    min-height: 20px;
                }}

                #2fa-section {{
                    display: none;
                    margin-top: 30px;
                    padding-top: 30px;
                    border-top: 2px solid #eee;
                }}

                #2fa-section.active {{
                    display: block;
                }}

                .input-group {{
                    margin: 20px 0;
                }}

                input[type="tel"] {{
                    width: 100%;
                    padding: 12px;
                    font-size: 24px;
                    text-align: center;
                    letter-spacing: 10px;
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    font-weight: bold;
                }}

                input[type="tel"]:focus {{
                    outline: none;
                    border-color: #667eea;
                }}

                .btn {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    margin-top: 10px;
                    width: 100%;
                    transition: all 0.3s ease;
                }}

                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
                }}

                .timer {{
                    color: #999;
                    font-size: 12px;
                    margin-top: 10px;
                }}

                .success {{
                    color: #28a745;
                    font-size: 16px;
                }}

                .error {{
                    color: #dc3545;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h2>🔐 Authenticating</h2>
                <p id="status">Opening Uber login...</p>

                <div id="2fa-section">
                    <h3>📱 Enter Verification Code</h3>
                    <p>We've sent a code to your phone or email</p>
                    <div class="input-group">
                        <input type="tel" id="2fa-code" maxlength="6" placeholder="000000" autocomplete="off">
                    </div>
                    <button class="btn" onclick="submit2FA()">Verify Code</button>
                    <div class="timer">
                        <p>Code expires in: <span id="timer">5:00</span></p>
                    </div>
                </div>
            </div>

            <script>
                const uid = "{uid}";
                let timeRemaining = 300;
                let authCheckInterval;

                // Poll for auth status
                function checkAuthStatus() {{
                    fetch(`/auth-status?uid=${{uid}}`)
                        .then(r => r.json())
                        .then(data => {{
                            const status = data.status;
                            const message = data.message;

                            document.getElementById('status').textContent = message;

                            if (status === 'waiting_2fa') {{
                                document.getElementById('2fa-section').classList.add('active');
                                document.getElementById('2fa-code').focus();
                            }} else if (status === 'completed') {{
                                document.getElementById('status').innerHTML = '<span class="success">✅ Authentication successful!</span>';
                                clearInterval(authCheckInterval);
                                setTimeout(() => {{
                                    window.location.href = '/?uid=' + uid;
                                }}, 2000);
                            }} else if (status === 'failed') {{
                                document.getElementById('status').innerHTML = '<span class="error">❌ Authentication failed. Please try again.</span>';
                                clearInterval(authCheckInterval);
                            }}
                        }})
                        .catch(err => console.error('Error checking status:', err));
                }}

                function submit2FA() {{
                    const code = document.getElementById('2fa-code').value;
                    if (code.length !== 6) {{
                        alert('Please enter a 6-digit code');
                        return;
                    }}

                    fetch('/submit-2fa-code', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{uid: uid, code: code}})
                    }})
                    .then(r => r.json())
                    .then(data => {{
                        if (data.success) {{
                            document.getElementById('status').innerHTML = '<span class="success">✅ Code verified!</span>';
                        }} else {{
                            alert('Invalid code. Please try again.');
                        }}
                    }})
                    .catch(err => console.error('Error:', err));
                }}

                function updateTimer() {{
                    const mins = Math.floor(timeRemaining / 60);
                    const secs = timeRemaining % 60;
                    document.getElementById('timer').textContent = 
                        mins + ':' + (secs < 10 ? '0' : '') + secs;
                    timeRemaining--;

                    if (timeRemaining < 0) {{
                        clearInterval(timerInterval);
                    }}
                }}

                // Start polling
                authCheckInterval = setInterval(checkAuthStatus, 1000);
                checkAuthStatus();

                // Start timer
                const timerInterval = setInterval(updateTimer, 1000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(html)

    except Exception as e:
        logger.error(f"Error in auth_page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth-status")
async def get_auth_status(uid: str):
    """Get current authentication status."""
    try:
        user_data = load_user_data(uid)
        status = user_data.get("auth_status", "not_authenticated")

        messages = {
            "not_authenticated": "🔐 Please authenticate your Uber account",
            "waiting_login": "🔐 Logging in...",
            "waiting_2fa": "📱 2FA code required",
            "completed": "✅ Authentication successful!",
            "failed": "❌ Authentication failed",
        }

        return {
            "status": status,
            "message": messages.get(status, "Unknown status"),
        }

    except Exception as e:
        logger.error(f"Error getting auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-2fa-code")
async def submit_2fa_code(request: TwoFARequest):
    """Submit 2FA code from user."""
    try:
        # Validate code format
        if not request.code or len(request.code) < 4 or len(request.code) > 8:
            return {"success": False, "message": "Invalid code format"}

        # Submit code to auth manager
        success = await auth_manager.submit_2fa_code(request.uid, request.code)

        if success:
            return {"success": True, "message": "Code submitted"}
        else:
            return {"success": False, "message": "No active authentication session"}

    except Exception as e:
        logger.error(f"Error submitting 2FA code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/setup-completed")
async def setup_completed(uid: str):
    """Check if user has completed setup."""
    try:
        user_data = load_user_data(uid)
        is_authenticated = user_data.get("uber_authenticated", False)

        return {
            "is_setup_completed": is_authenticated,
            "auth_status": user_data.get("auth_status", "not_authenticated"),
        }

    except Exception as e:
        logger.error(f"Error checking setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBHOOK - VOICE TRIGGER DETECTION & BOOKING
# ============================================================================


async def _process_booking(uid: str, segments: list, background_tasks: BackgroundTasks):
    """Process booking immediately when trigger is detected."""
    # Join all segment texts
    combined_text = " ".join([seg.get("text", "") if isinstance(seg, dict) else seg.text for seg in segments])
    logger.info(f"✅ Joined text: '{combined_text}'")
    
    # Detect trigger phrase and extract locations (using LLM, no strict patterns)
    is_trigger, start_location, end_location = await detect_trigger_and_destinations(segments)
    
    if not is_trigger:
        logger.info(f"❌ LLM determined this is not a ride booking request for {uid}")
        active_bookings[uid] = False
        return
    
    logger.info(f"✅ LLM validation passed for {uid}: {start_location} → {end_location}")
    
    if not start_location or not end_location:
        logger.warning(f"⚠️ Could not extract locations for {uid}")
        active_bookings[uid] = False
        return
    
    # Validate session
    user_data = load_user_data(uid)
    if not user_data.get("uber_authenticated"):
        logger.warning(f"⚠️ User {uid} not authenticated")
        active_bookings[uid] = False
        return
    
    # Check rate limiting
    current_time = time.time()
    if uid in last_booking_time:
        time_since_last = current_time - last_booking_time[uid]
        if time_since_last < MIN_BOOKING_INTERVAL:
            logger.info(f"⏱️ Rate limited for {uid}")
            active_bookings[uid] = False
            return
    
    # Record booking time
    last_booking_time[uid] = current_time
    
    logger.info(f"🔒 Booking marked as ACTIVE for {uid} (LLM validated)")
    
    # Book ride in background
    background_tasks.add_task(
        _book_ride_background,
        uid,
        start_location,
        end_location,
    )
    logger.info(f"🚗 Starting booking immediately for {uid}: {start_location} → {end_location}")


async def _process_bucket_delayed(uid: str):
    """
    Keep checking if 5 seconds have passed since last segment.
    Only process when 5 seconds of silence detected.
    """
    logger.info(f"⏳ Monitoring bucket for {uid}")
    
    while True:
        await asyncio.sleep(0.5)  # Check every 500ms
        
        # If bucket was cleared, we're done
        if uid not in segment_buckets:
            logger.info(f"✅ Bucket for {uid} already processed")
            return
        
        # Check if 5 seconds have passed since last segment
        last_arrival = segment_last_arrival.get(uid, time.time())
        time_since_last = time.time() - last_arrival
        
        if time_since_last >= BUCKET_WAIT_TIME:
            # 5 seconds of silence detected, process now
            logger.info(f"✅ 5 seconds of silence detected for {uid}")
            break
    
    # Get segments before clearing
    if uid not in segment_buckets:
        return
    
    segments = segment_buckets[uid]
    logger.info(f"🔄 Processing bucket for {uid} with {len(segments)} segment(s)")
    
    # Clear bucket and timer
    del segment_buckets[uid]
    if uid in segment_last_arrival:
        del segment_last_arrival[uid]
    if uid in bucket_timers:
        del bucket_timers[uid]
    logger.info(f"🗑️ Cleared bucket for {uid}")
    
    # Join all segment texts
    combined_text = " ".join([seg.get("text", "") if isinstance(seg, dict) else seg.text for seg in segments])
    logger.info(f"✅ Joined text: '{combined_text}'")
    
    # Detect trigger phrase and extract locations (using LLM, no strict patterns)
    is_trigger, start_location, end_location = await detect_trigger_and_destinations(segments)
    
    if not is_trigger:
        logger.info(f"❌ LLM determined this is not a ride booking request for {uid}")
        return
    
    logger.info(f"✅ LLM validation passed for {uid}: {start_location} → {end_location}")
    
    # If only destination provided, get pickup from user's current location
    if not start_location and end_location:
        logger.info(f"📍 Only destination provided, getting pickup from user's location...")
        # Get GPS coordinates from stored bucket data
        gps_lat = segment_buckets.get(f"{uid}_gps_lat")
        gps_lon = segment_buckets.get(f"{uid}_gps_lon")
        
        if gps_lat and gps_lon:
            logger.info(f"📍 Using GPS coordinates: ({gps_lat}, {gps_lon})")
        else:
            logger.info(f"📍 No GPS provided, using San Francisco fallback")
        
        logger.info(f"🔄 Starting geolocation process...")
        logger.info(f"   1️⃣ Getting landmark...")
        start_location = await get_pickup_location_from_ip(None, gps_lat, gps_lon)
        if start_location:
            logger.info(f"✅ Got pickup location: {start_location}")
            logger.info(f"📍 Pickup location determined: {start_location}")
            logger.info(f"🎯 Final booking route: {start_location} → {end_location}")
        else:
            logger.warning(f"⚠️ Could not get pickup location")
            logger.warning(f"⚠️ Skipping booking - no pickup location available")
            return
    
    if not start_location or not end_location:
        logger.warning(f"⚠️ Could not extract locations for {uid}")
        return
    
    # Validate session
    user_data = load_user_data(uid)
    if not user_data.get("uber_authenticated"):
        logger.warning(f"⚠️ User {uid} not authenticated")
        return
    
    # Check rate limiting
    current_time = time.time()
    if uid in last_booking_time:
        time_since_last = current_time - last_booking_time[uid]
        if time_since_last < MIN_BOOKING_INTERVAL:
            logger.info(f"⏱️ Rate limited for {uid}")
            return
    
    # Record booking time
    last_booking_time[uid] = current_time
    
    logger.info(f"🔒 Booking marked as ACTIVE for {uid} (LLM validated)")
    logger.info(f"🚗 Starting booking immediately for {uid}: {start_location} → {end_location}")
    
    # Book ride directly (no background task)
    success, message, driver, eta = await uber_automation.book_ride(
        uid, start_location, end_location, auto_request=True
    )
    
    # Check if login button was found (indicates authentication issue)
    if "login button" in message.lower() or "not authenticated" in message.lower():
        logger.warning(f"⚠️ FOUND LOGIN BUTTON IN DOM - User {uid} may not be authenticated!")
        logger.warning(f"⚠️ Please visit: http://localhost:8000/auth?uid={uid} to re-authenticate")
    
    logger.info(f"📊 Booking result for {uid}: success={success}, message={message}, driver={driver}, eta={eta}")
    
    # Mark booking as inactive
    active_bookings[uid] = False
    logger.info(f"🔓 Marking booking as inactive for {uid}")


@app.post("/webhook")
async def webhook(request: Request):
    """
    Receive voice transcripts from Omi.
    Collect segments for 5 seconds, then process if trigger detected.
    Always uses default_user.
    Extracts phone's IP address from request for geolocation.
    """
    try:
        # Extract phone's IP address from request
        phone_ip = request.client.host if request.client else None
        logger.info(f"📱 Webhook received from IP: {phone_ip}")
        
        # Handle both Pydantic model and raw JSON/streaming data
        try:
            body = await request.json()
        except:
            body = await request.body()
            if isinstance(body, bytes):
                body = json.loads(body.decode())
        
        # Always use default_user
        uid = "default_user"
        segments = body.get("segments", [])
        
        # Optional: Extract GPS coordinates if provided in webhook
        gps_lat = body.get("gps_lat")
        gps_lon = body.get("gps_lon")
        if gps_lat and gps_lon:
            logger.info(f"📍 GPS coordinates provided: ({gps_lat}, {gps_lon})")
        
        # Store phone IP in request context for later use
        request.state.phone_ip = phone_ip
        request.state.gps_lat = gps_lat
        request.state.gps_lon = gps_lon
        
        if not segments:
            logger.error("❌ No segments provided in request")
            return {
                "message": "❌ Missing segments",
                "booked": False,
            }
        
        # Convert dict segments to proper format if needed
        if segments and isinstance(segments[0], dict):
            segments = [{"text": s.get("text", ""), "speaker": s.get("speaker", "")} for s in segments]
        
        logger.info(f"📥 Webhook received for uid={uid}")
        logger.info(f"📊 Payload: {len(segments)} segment(s)")
        for i, seg in enumerate(segments, 1):
            text = seg.get("text", "") if isinstance(seg, dict) else seg.text
            speaker = seg.get("speaker", "") if isinstance(seg, dict) else seg.speaker
            logger.info(f"  Segment {i}: speaker='{speaker}', text='{text}'")
        
        # Initialize bucket if needed
        if uid not in segment_buckets:
            segment_buckets[uid] = []
            logger.info(f"🆕 Creating new bucket for {uid}")
            # Store phone IP for geolocation
            segment_buckets[f"{uid}_phone_ip"] = phone_ip
            # Store GPS coordinates if provided
            segment_buckets[f"{uid}_gps_lat"] = gps_lat
            segment_buckets[f"{uid}_gps_lon"] = gps_lon
            # Start monitoring task on first segment
            task = asyncio.create_task(_process_bucket_delayed(uid))
            bucket_timers[uid] = task
            logger.info(f"🔄 Started monitoring task for {uid}")
        
        # Add segments to bucket
        segment_buckets[uid].extend(segments)
        logger.info(f"✅ Added {len(segments)} segment(s) to bucket")
        logger.info(f"📊 Bucket now has {len(segment_buckets[uid])} total segment(s)")
        
        # Update last arrival time (sliding window)
        segment_last_arrival[uid] = time.time()
        logger.info(f"⏱️ Last segment at {segment_last_arrival[uid]}, waiting {BUCKET_WAIT_TIME}s from now...")
        
        return {
            "message": f"📝 Received {len(segments)} segment(s). Processing in {BUCKET_WAIT_TIME}s...",
            "booked": False,
            "batching": True,
        }

    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return {
            "message": f"❌ Error processing request: {str(e)}",
            "booked": False,
        }


async def _book_ride_background(uid: str, start_location: str, end_location: str):
    """Background task to book ride."""
    try:
        logger.info(f"Starting booking for {uid}: {start_location} → {end_location}")
        # Get auto_request from environment variable (default: False)
        auto_request_env = os.getenv("AUTO_REQUEST", "false")
        auto_request = auto_request_env.lower() == "true"
        logger.info(f"🔧 AUTO_REQUEST configuration:")
        logger.info(f"   - Environment variable: '{auto_request_env}'")
        logger.info(f"   - Parsed value: {auto_request}")
        logger.info(f"   - Auto-request enabled: {'✅ YES' if auto_request else '❌ NO'}")
        success, message, driver_name, eta = await uber_automation.book_ride(
            uid, start_location, end_location, auto_request=auto_request
        )
        logger.info(f"Booking result for {uid}: success={success}, message={message}, driver={driver_name}, eta={eta}")
        
        # Record booking if successful
        if success:
            from simple_storage import record_booking
            record_booking(uid, f"{start_location} → {end_location}", driver_name, eta)
            logger.info(f"Booking recorded for {uid}")
        else:
            logger.warning(f"Booking failed for {uid}: {message}")
    except Exception as e:
        logger.error(f"Error booking ride: {e}", exc_info=True)


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    logger.info("Omi Uber App starting up...")
    # Ensure storage directories exist
    from simple_storage import ensure_dirs
    ensure_dirs()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Omi Uber App shutting down...")
    # Close any active browsers
    for uid in list(active_browsers.keys()):
        try:
            await auth_manager._cleanup_browser(uid)
        except Exception as e:
            logger.error(f"Error cleaning up browser for {uid}: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
