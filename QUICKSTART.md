# 🚀 Quick Start Guide

Get the Omi Uber App running in 5 minutes! 🚀

Get the Omi Uber App running in 5 minutes!

## Prerequisites

- Python 3.10+
- OpenAI API key (get one at https://platform.openai.com)
- Git

## Local Development (5 minutes)

### 1. Clone & Setup
```bash
cd /Users/spartan/CascadeProjects/omi-uber-app
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and AUTO_REQUEST setting
```

**Example .env:**
```
OPENAI_API_KEY=sk-proj-xxxxx
AUTO_REQUEST=false    # Set to true to auto-book rides
```

### 4. Run the App
```bash
uvicorn main:app --reload
```

Visit: **http://localhost:8000**

---

## Docker Development (3 minutes)

### 1. Build & Run
```bash
docker-compose up --build
```

### 2. Access
Visit: **http://localhost:8000**

---

## Testing the App

### 1. Home Page
- Visit http://localhost:8000
- Should see "Connect Uber Account" button

### 2. Authentication Flow
- Click "Connect Uber Account"
- Browser will open Uber login
- Enter your Uber credentials
- If 2FA required, enter code in the app
- Should redirect to home with "✅ Uber Connected"

### 3. Voice Booking (via API)
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "segments": [
      {"text": "book an uber to san francisco airport", "speaker": "user"}
    ]
  }'
```

### 4. Check Status
```bash
curl http://localhost:8000/auth-status?uid=test_user
```

---

## Deployment to Railway

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login & Create Project
```bash
railway login
railway init
```

### 3. Set Environment Variables
```bash
railway variables set OPENAI_API_KEY=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
```

### 4. Deploy
```bash
railway up
```

Your app will be live at: `https://your-project.railway.app`

---

## Deployment to Heroku

### 1. Install Heroku CLI
```bash
brew tap heroku/brew && brew install heroku
```

### 2. Login & Create App
```bash
heroku login
heroku create your-app-name
```

### 3. Set Environment Variables
```bash
heroku config:set OPENAI_API_KEY=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
```

### 4. Deploy
```bash
git push heroku main
```

Your app will be live at: `https://your-app-name.herokuapp.com`

---

## Omi Integration

### 1. Get Your App URL
- Local: `http://localhost:8000`
- Production: `https://your-app.railway.app`

### 2. Configure in Omi App
In the Omi app settings, add these URLs:

- **App Home URL**: `https://your-app.railway.app/`
- **Auth URL**: `https://your-app.railway.app/auth`
- **Setup Completed URL**: `https://your-app.railway.app/setup-completed`
- **Webhook URL**: `https://your-app.railway.app/webhook`

### 3. Test Voice Command
Say to your Omi device:
> "Book an Uber to San Francisco Airport"

---

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
# Check if .env file exists and has the key
cat .env

# Or set it directly
export OPENAI_API_KEY=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
```

### "Playwright not installed"
```bash
playwright install chromium
```

### "Port 8000 already in use"
```bash
# Use a different port
uvicorn main:app --port 8001
```

### "Browser automation timeout"
- Check internet connection
- Verify Uber website is accessible
- Try re-authenticating

### "2FA not detected"
- Make sure you're using a real Uber account
- Check if Uber's UI has changed (selectors may need updating)
- Try manual authentication first

---

## File Locations

- **User Data**: `users/{uid}.json`
- **Sessions**: `sessions/{uid}_uber_session.json`
- **Logs**: Console output (or use logging module)

---

## API Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Home page |
| GET | `/auth` | Start authentication |
| GET | `/auth-status` | Check auth progress |
| POST | `/submit-2fa-code` | Submit 2FA code |
| GET | `/setup-completed` | Check if authenticated |
| POST | `/webhook` | Book ride from voice |
| GET | `/health` | Health check |

---

## Next Steps

1. ✅ Get app running locally
2. ✅ Test authentication flow
3. ✅ Test voice booking via API
4. ✅ Deploy to Railway/Heroku
5. ✅ Configure in Omi app
6. ✅ Test voice commands on device

---

## Support

- Check README.md for detailed documentation
- Review test_app.py for usage examples
- Check logs for error messages
- Verify environment variables are set

---

**Happy voice-activated Uber booking! 🚗**
