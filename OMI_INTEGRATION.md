# Omi Integration Guide 🔗

Complete guide to integrate the Omi Uber App with your Omi device.

## Overview

The Omi Uber App provides endpoints that integrate seamlessly with the Omi platform for voice-activated Uber booking.

## Required Endpoints

### 1. App Home URL
**Endpoint**: `GET /`

**Purpose**: Display app status and connection button

**Query Parameters**:
- `uid` - User ID (optional, defaults to "default_user")

**Response**: HTML page showing:
- ✅ If authenticated: "Uber Connected" with usage instructions
- ⏳ If waiting for 2FA: "Waiting for verification" with code input
- 🔐 If not authenticated: "Connect Uber Account" button

**Example**:
```
https://your-app.railway.app/?uid=user123
```

---

### 2. Auth URL
**Endpoint**: `GET /auth`

**Purpose**: Launch one-time authentication flow

**Query Parameters**:
- `uid` - User ID (optional)

**Flow**:
1. Opens browser with Uber login page
2. User enters credentials
3. If 2FA required, shows code input interface
4. Saves session after successful authentication
5. Redirects back to home page

**Example**:
```
https://your-app.railway.app/auth?uid=user123
```

---

### 3. Setup Completed URL
**Endpoint**: `GET /setup-completed`

**Purpose**: Check if user has completed authentication

**Query Parameters**:
- `uid` - User ID (required)

**Response**:
```json
{
  "is_setup_completed": true,
  "auth_status": "completed"
}
```

**Example**:
```
https://your-app.railway.app/setup-completed?uid=user123
```

---

### 4. Webhook URL
**Endpoint**: `POST /webhook`

**Purpose**: Receive voice transcripts and book rides

**Request Format**:
```json
{
  "uid": "user123",
  "segments": [
    {
      "text": "book an uber to san francisco airport",
      "speaker": "user"
    }
  ]
}
```

**Response**:
```json
{
  "message": "🚗 Booking Uber to San Francisco Airport...",
  "booked": true,
  "destination": "San Francisco Airport"
}
```

**Supported Phrases**:
- "Book an Uber to [destination]"
- "Get me a ride to [destination]"
- "Call an Uber to [destination]"
- "Request an Uber to [destination]"
- "Order an Uber to [destination]"

**Example**:
```bash
curl -X POST https://your-app.railway.app/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user123",
    "segments": [
      {"text": "book an uber to downtown", "speaker": "user"}
    ]
  }'
```

---

## Omi App Configuration

### Step 1: Deploy the App

Choose one of these options:

#### Option A: Railway (Recommended)
```bash
railway login
railway init
railway variables set OPENAI_API_KEY=your_key
railway up
```

#### Option B: Heroku
```bash
heroku login
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

#### Option C: Local Testing
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app
```

### Step 2: Get Your Base URL

- **Railway**: `https://your-project.railway.app`
- **Heroku**: `https://your-app-name.herokuapp.com`
- **Local**: `http://localhost:8000`

### Step 3: Configure in Omi App

In the Omi app settings, configure these URLs:

```
App Home URL:
https://your-app.railway.app/

Auth URL:
https://your-app.railway.app/auth

Setup Completed URL:
https://your-app.railway.app/setup-completed

Webhook URL:
https://your-app.railway.app/webhook
```

### Step 4: Test Connection

1. Open Omi app
2. Navigate to Uber integration
3. Click "Connect Uber Account"
4. Complete authentication (including 2FA if prompted)
5. Should see "✅ Uber Connected"

### Step 5: Test Voice Command

Say to your Omi device:
> "Book an Uber to San Francisco Airport"

You should receive a notification with the booking confirmation.

---

## User ID Handling

The `uid` parameter identifies users and stores their sessions separately.

### Automatic User ID
If not provided, defaults to `"default_user"`

### Custom User ID
Pass `uid` as query parameter:
```
https://your-app.railway.app/?uid=john_doe
https://your-app.railway.app/auth?uid=john_doe
```

### Multiple Users
Each user has:
- Separate session file: `sessions/{uid}_uber_session.json`
- Separate user data: `users/{uid}.json`
- Independent authentication status

---

## Authentication Flow

### First-Time User

1. **User clicks "Connect Uber Account"**
   - Redirects to `/auth?uid=user123`

2. **Browser opens Uber login**
   - User enters email/password

3. **2FA Detection**
   - App detects if 2FA is required
   - Shows code input interface if needed

4. **User enters 2FA code**
   - Submits via `/submit-2fa-code` endpoint
   - App verifies and continues

5. **Session saved**
   - Browser session stored with cookies/localStorage
   - User redirected to home: "✅ Connected"

### Subsequent Bookings

1. **User says voice command**
   - "Book an Uber to [destination]"

2. **Omi sends to webhook**
   - POST `/webhook` with transcribed text

3. **App processes**
   - Detects trigger phrase
   - Extracts destination using OpenAI
   - Validates saved session
   - Books ride using headless browser

4. **User receives notification**
   - "🚗 Booked to [destination]! ETA: [time]"

---

## 2FA Handling

### Automatic Detection

The app automatically detects 2FA by looking for:
- SMS code input fields
- Authenticator app prompts
- "Verify" buttons
- Code verification screens

### User Experience

1. **Login page appears**
   - User enters credentials

2. **2FA detected**
   - App pauses browser
   - UI updates to show code input

3. **User enters code**
   - 6-digit code from phone/email
   - Timeout: 5 minutes

4. **Code verified**
   - App continues authentication
   - Session saved
   - User redirected to home

### Security Features

- ✅ Rate limiting: Max 3 attempts per session
- ✅ Timeout: 5 minutes for code entry
- ✅ Code validation: 4-8 digit format
- ✅ Session encryption: Saved as JSON
- ✅ "Remember device" checkbox checked automatically

---

## Session Management

### Session Persistence

Sessions are saved after successful authentication:
- **Location**: `sessions/{uid}_uber_session.json`
- **Contains**: Cookies, localStorage, session state
- **Format**: Playwright storage state

### Session Validation

Before each booking:
1. Load saved session
2. Attempt to access Uber homepage
3. Check if still logged in
4. If expired: Prompt re-authentication

### Session Expiration

If session expires:
1. User sees: "⚠️ Please re-authenticate your Uber account"
2. Redirect to `/auth` for fresh login
3. Handle 2FA again if prompted
4. Save new session

---

## Error Handling

### Common Scenarios

**"No saved session"**
- User hasn't authenticated yet
- Solution: Click "Connect Uber Account"

**"Session expired"**
- Saved session no longer valid
- Solution: Re-authenticate via `/auth`

**"Could not extract destination"**
- Voice command unclear
- Solution: Speak more clearly with destination name

**"Security challenge detected"**
- Uber detected unusual activity
- Solution: Try again or re-authenticate

**"2FA timeout"**
- User didn't enter code within 5 minutes
- Solution: Start authentication again

### Error Messages

All errors return JSON with human-readable messages:

```json
{
  "message": "⚠️ Please re-authenticate your Uber account",
  "booked": false
}
```

---

## Testing

### Manual Testing

1. **Test home page**
   ```bash
   curl https://your-app.railway.app/
   ```

2. **Test auth status**
   ```bash
   curl https://your-app.railway.app/auth-status?uid=test_user
   ```

3. **Test webhook**
   ```bash
   curl -X POST https://your-app.railway.app/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "uid": "test_user",
       "segments": [{"text": "book an uber to downtown", "speaker": "user"}]
     }'
   ```

### Automated Testing

```bash
pytest test_app.py -v
```

---

## Deployment Checklist

- [ ] Deploy app to Railway/Heroku
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Test health check: `/health`
- [ ] Test home page: `/`
- [ ] Test authentication flow manually
- [ ] Configure URLs in Omi app
- [ ] Test voice command on device
- [ ] Monitor logs for errors
- [ ] Set up error alerts/monitoring

---

## Monitoring

### Health Check
```bash
curl https://your-app.railway.app/health
```

### View Logs

**Railway**:
```bash
railway logs
```

**Heroku**:
```bash
heroku logs --tail
```

**Local**:
```bash
# Check console output
```

### Metrics to Monitor

- Authentication success rate
- Average booking time
- 2FA detection accuracy
- Session expiration rate
- Error frequency

---

## Troubleshooting

### App not responding
1. Check deployment status
2. Verify environment variables
3. Check logs for errors
4. Restart the app

### Authentication fails
1. Verify Uber account is valid
2. Check internet connection
3. Try manual login first
4. Check if Uber UI has changed

### 2FA not detected
1. Verify 2FA is enabled on Uber account
2. Check if Uber's UI selectors have changed
3. Try manual authentication
4. Review logs for selector errors

### Voice booking fails
1. Check if user is authenticated
2. Verify destination extraction
3. Check if session is still valid
4. Review logs for booking errors

---

## Support

For issues:
1. Check README.md for detailed documentation
2. Review logs for error messages
3. Test endpoints manually with curl
4. Verify environment variables
5. Check Uber website is accessible

---

## Next Steps

1. ✅ Deploy app
2. ✅ Configure environment variables
3. ✅ Test endpoints manually
4. ✅ Configure in Omi app
5. ✅ Test voice commands
6. ✅ Monitor and optimize

---

**Ready to integrate? Let's go! 🚀**
