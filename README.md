# 🚗 Omi Uber App - Voice-Activated Ride Booking

Automated Uber ride booking via voice commands through the Omi device. Simply say "Book an Uber to [destination]" and the app handles the entire booking process. 🚗

A voice-activated Uber booking application for the Omi device with full 2FA support and browser automation.

## Features

✅ **Voice-Activated Booking** - Say "Book an Uber to [destination]" and ride is booked automatically
✅ **Sliding Window Segment Collection** - Collects voice segments for 5 seconds of silence before processing
✅ **LLM-Powered Destination Extraction** - Corrects spelling mistakes, ignores generic terms (Current Location, Office, Home)
✅ **One-Time Authentication** - Authenticate once, never login again
✅ **Session Persistence** - Saves authenticated session for future bookings
✅ **Browser Automation** - Uses Playwright to automate Uber booking
✅ **Screenshot Capture** - Captures screenshots at each booking step in `/snapshots` folder
✅ **Real-Time Status** - Live authentication status updates
✅ **Error Handling** - Graceful error messages and recovery
✅ **Login Detection** - Warns if login button detected (authentication issue)

## Tech Stack

- **FastAPI** - Modern async web framework
- **Playwright** - Browser automation
- **OpenAI API** - Destination extraction from voice
- **Python 3.10+** - Async/await support
- **Railway** - Cloud deployment

## Project Structure

```
omi-uber-app/
├── main.py                 # FastAPI app with all endpoints
├── auth_manager.py         # 2FA handling and session management
├── uber_automation.py      # Playwright browser automation
├── ride_detector.py        # AI-powered trigger & destination detection
├── simple_storage.py       # File-based user storage
├── requirements.txt        # Python dependencies
├── railway.toml            # Railway deployment config
├── Procfile                # Heroku/Railway process file
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation

### Local Development

1. **Clone the repository**
```bash
git clone <repo-url>
cd omi-uber-app
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. **Run the app**
```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required for destination extraction)
- `PORT` - Server port (default: 8000)
- `PLAYWRIGHT_BROWSERS_PATH` - Path to Playwright browsers (default: auto)
- `AUTO_REQUEST` - Auto-book rides (default: false). Set to `true` to automatically click "Request" button

**Example .env:**
```
OPENAI_API_KEY=sk-proj-xxxxx
PORT=8000
AUTO_REQUEST=false
```

## API Endpoints

### GET `/`
Home page showing authentication status and usage instructions.

**Query Parameters:**
- `uid` - User ID (optional, defaults to "default_user")

**Response:** HTML page with status and connection button

---

### GET `/auth`
Launch the authentication flow.

**Query Parameters:**
- `uid` - User ID (optional)

**Flow:**
1. Opens Uber login page in browser
2. Detects if 2FA is required
3. Shows 2FA code input if needed
4. Saves session after successful authentication
5. Redirects to home page

---

### GET `/auth-status`
Get current authentication status (for real-time updates).

**Query Parameters:**
- `uid` - User ID (required)

**Response:**
```json
{
  "status": "waiting_2fa|completed|failed|waiting_login",
  "message": "Human-readable status message"
}
```

---

### POST `/submit-2fa-code`
Submit 2FA code during authentication.

**Request Body:**
```json
{
  "uid": "user123",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Code submitted"
}
```

---

### GET `/setup-completed`
Check if user has completed authentication setup.

**Query Parameters:**
- `uid` - User ID (required)

**Response:**
```json
{
  "is_setup_completed": true,
  "auth_status": "completed"
}
```

---

### POST `/webhook`
Receive voice transcripts from Omi and book rides.

**Behavior:**
- Collects segments for 5 seconds of silence (sliding window)
- Each new segment restarts the 5-second countdown
- After 5 seconds of silence, processes all collected segments
- Validates user is authenticated before booking
- Extracts locations using LLM (ignores spelling mistakes)
- Automatically books ride if valid locations detected

**Request Body:**
```json
{
  "segments": [
    {
      "text": "book an uber",
      "speaker": "user"
    }
  ]
}
```

**Note:** `uid` is ignored - always uses `default_user`

**Response:**
```json
{
  "message": "📝 Received 1 segment(s). Processing in 5s...",
  "booked": false,
  "batching": true
}
```

**Example Flow:**
```bash
# Segment 1 at t=0
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "Book an Uber", "speaker": "user"}]}'

# Segment 2 at t=2 (timer restarts to t=7)
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"segments": [{"text": "from SJSU to Cal Train Station", "speaker": "user"}]}'

# Wait 5 seconds → processes at t=7
# Result: Joins segments, validates with LLM, books ride
```

---

### GET `/health`
Health check endpoint for deployment monitoring.

**Response:**
```json
{
  "status": "ok",
  "service": "omi-uber-app"
}
```

## Authentication Flow

### First-Time Setup

1. User clicks "Connect Uber Account"
2. Browser opens Uber login page
3. User enters email/password
4. If 2FA required:
   - App detects 2FA prompt
   - Shows code input interface
   - User enters 6-digit code
   - App verifies and continues
5. Session saved with cookies/localStorage
6. User redirected to home: "✅ Connected"

### Subsequent Bookings

1. User says "Book an Uber to [destination]"
2. App detects trigger phrase
3. Extracts destination using OpenAI
4. Validates saved session is still active
5. Launches headless browser with saved session
6. Fills destination and clicks "Request UberX"
7. Extracts driver name and ETA
8. Notifies user with ride details

### Session Validation

Before each booking:
- Loads saved session (cookies + localStorage)
- Attempts to access Uber homepage
- If login required: Prompts user to re-authenticate
- If successful: Proceeds with booking

## 2FA Handling

### Detection
The app detects 2FA prompts by looking for:
- `input[type="tel"]`
- `input[placeholder*="code"]`
- `input[placeholder*="verification"]`
- `button:has-text("Verify")`

### Flow
1. Browser pauses at 2FA prompt
2. UI updates to show code input field
3. User enters code (up to 5 minutes)
4. App fills code and submits
5. Waits for verification
6. Saves complete authenticated session

### Security
- Rate limiting: Max 3 attempts per session
- Timeout: 5 minutes for code entry
- Code validation: 4-8 digit format
- Session encryption: Saved as JSON with cookies

## Voice Segment Collection

### Sliding Window Logic
The webhook uses a **sliding window** to collect voice segments:

1. **First segment arrives** → Create bucket, start monitoring task
2. **New segments arrive** → Add to bucket, update last arrival time
3. **Monitor checks every 500ms** → When 5 seconds pass since last segment, process
4. **Processing** → Join all segments, validate with LLM, extract locations, book ride

**Example Timeline:**
```
t=0s: Segment 1 arrives ("Book an Uber")
      → Last arrival = 0s, waiting until 5s

t=2s: Segment 2 arrives ("from SJSU to Cal Train")
      → Last arrival = 2s, waiting until 7s

t=7s: 5 seconds of silence detected
      → Process: "Book an Uber from SJSU to Cal Train"
      → Extract: SJSU → Cal Train
      → Book ride
```

### Destination Extraction

**LLM Validation Rules:**
- ✅ Extracts actual location names (SJSU, Cal Train Station, Downtown)
- ✅ Corrects spelling mistakes (SJS → SJSU, Cal Trane → Cal Train)
- ❌ Rejects generic terms (Current Location, Office, Home, My Place, Work)
- ✅ Returns both start and end locations
- ✅ Handles single location (uses as end location only)

**Supported Phrases:**
- "Book an Uber to [destination]"
- "Get me a ride to [destination]"
- "Call an Uber to [destination]"
- "Request an Uber to [destination]"
- "Order an Uber to [destination]"

**Example Inputs:**
```
Input: "Book an Uber from SJS to Cal Trane Station"
Output: SJSU → Cal Train Station

Input: "Book an Uber from my office to downtown"
Output: ❌ Rejected (generic terms)

Input: "Book an Uber to the airport"
Output: ✅ Extracted (airport is a valid location)
```

## Deployment

### Railway

1. **Connect repository**
```bash
railway link
```

2. **Set environment variables**
```bash
railway variables set OPENAI_API_KEY=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
```

3. **Deploy**
```bash
railway up
```

The app will be available at `https://your-project.railway.app`

### Heroku

1. **Create app**
```bash
heroku create your-app-name
```

2. **Set environment variables**
```bash
heroku config:set OPENAI_API_KEY=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
```

3. **Deploy**
```bash
git push heroku main
```

### Docker

```bash
docker build -t omi-uber-app .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key omi-uber-app
```

## Booking Screenshots

The system captures screenshots at each step of the booking process and stores them in the `/snapshots` folder.

### Screenshot Sequence
```
snapshots/
  └── default_user/
      ├── 01_pickup_filled.png          # After entering pickup location
      ├── 02_pickup_selected.png        # After selecting pickup suggestion
      ├── 03_dropoff_filled.png         # After entering dropoff location
      ├── 04_dropoff_selected.png       # After selecting dropoff suggestion
      ├── 05_ride_details.png           # Ride details page
      ├── 06_ride_options.png           # Available ride options
      ├── 07_ride_selected.png          # After selecting a ride
      └── 08_booking_confirmation.png   # After clicking request button
```

### Usage
Screenshots are automatically captured during each booking. Use them for:
- Debugging booking issues
- Verifying automation steps
- Monitoring ride selection
- Confirming successful bookings

## File Storage

### User Data
- Location: `users/{uid}.json`
- Contains: Authentication status, last booking, preferences
- Format: JSON

### Sessions
- Location: `sessions/{uid}_uber_session.json`
- Contains: Cookies, localStorage, session state
- Format: Playwright storage state

### Screenshots
- Location: `snapshots/{uid}/`
- Contains: Step-by-step booking process images
- Format: PNG images

## Error Handling

### Common Issues

**"No saved session"**
- User hasn't authenticated yet
- Solution: Click "Connect Uber Account"

**"Session expired"**
- Saved session is no longer valid
- Solution: Re-authenticate via /auth

**"Could not extract destination"**
- Voice command didn't contain clear destination
- Solution: Speak more clearly with destination name

**"Security challenge detected"**
- Uber detected unusual activity
- Solution: Try again or re-authenticate

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black *.py
flake8 *.py
```

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- ✅ Session files stored locally (not in version control)
- ✅ 2FA codes never logged
- ✅ API keys stored in environment variables
- ✅ HTTPS enforced in production
- ✅ Rate limiting on 2FA endpoint
- ✅ Timeout on authentication (5 minutes)
- ✅ Session validation before each booking

## Limitations

- Uber has no public API - uses browser automation
- Requires Chromium browser (installed by Playwright)
- 2FA detection based on common selectors (may vary)
- Headless mode may trigger security challenges
- Session persistence depends on Uber's session management

## Support

For issues or questions:
1. Check the logs: `docker logs <container-id>`
2. Verify environment variables are set
3. Ensure Playwright browsers are installed
4. Check OpenAI API key is valid

## License

MIT License - feel free to use and modify

## Acknowledgments

Based on the [BasedHardware Omi Slack App](https://github.com/BasedHardware/omi-slack-app)

---

**Built with ❤️ for voice-activated transportation**
