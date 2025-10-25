# Testing & Deployment Guide 🚀

Complete guide for testing locally and deploying to Railway for Omi integration.

---

## Part 1: Local Testing (Without Omi Device)

### Setup Local Environment

```bash
# 1. Setup
./setup.sh
source venv/bin/activate

# 2. Add OPENAI_API_KEY
nano .env
# Add: OPENAI_API_KEY=sk-...

# 3. Run locally
uvicorn main:app --reload
```

Your app is now at: `http://localhost:8000`

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{"status": "ok", "service": "omi-uber-app"}
```

### Test 2: Home Page

```bash
curl http://localhost:8000/?uid=test_user
```

**Expected**: HTML page with "Connect Uber Account" button

### Test 3: Authentication Flow

1. Visit: `http://localhost:8000/auth?uid=test_user`
2. Browser opens Uber login page
3. Enter your Uber credentials
4. If 2FA required, enter code in the app
5. Should redirect to home with "✅ Uber Connected"

### Test 4: Check Auth Status

```bash
curl http://localhost:8000/auth-status?uid=test_user
```

**Expected Response**:
```json
{
  "status": "completed",
  "message": "✅ Authentication successful!"
}
```

### Test 5: Test Webhook (Voice Booking)

**Test without trigger phrase**:
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "segments": [{"text": "hello world", "speaker": "user"}]
  }'
```

**Expected Response**:
```json
{"message": "No trigger phrase detected", "booked": false}
```

**Test with trigger phrase (FROM → TO)**:
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "segments": [{"text": "book an uber from downtown to the airport", "speaker": "user"}]
  }'
```

**Expected Response**:
```json
{
  "message": "🚗 Booking Uber from downtown to the airport...",
  "booked": true,
  "start_location": "downtown",
  "end_location": "the airport"
}
```

### Test 6: 2FA Code Submission

```bash
curl -X POST http://localhost:8000/submit-2fa-code \
  -H "Content-Type: application/json" \
  -d '{"uid": "test_user", "code": "123456"}'
```

---

## Part 2: Deploy to Railway

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Verify email
4. Create new project

### Step 2: Prepare GitHub Repository

```bash
cd /Users/spartan/CascadeProjects/omi-uber-app

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Omi Uber App with 2FA support"

# Create GitHub repository (via GitHub web)
# Then push
git remote add origin https://github.com/YOUR_USERNAME/omi-uber-app.git
git branch -M main
git push -u origin main
```

### Step 3: Connect Railway to GitHub

1. Go to Railway dashboard
2. Click "New Project"
3. Select "GitHub Repo"
4. Choose your `omi-uber-app` repository
5. Click "Deploy"

Railway will automatically detect the Python project and start building.

### Step 4: Set Environment Variables

**In Railway Dashboard**:

1. Go to your project
2. Click "Variables" tab
3. Add:
   ```
   OPENAI_API_KEY = sk-...
   PORT = 8000
   ```
4. Click "Save"

### Step 5: Wait for Deployment

Railway will:
1. Install dependencies from `requirements.txt`
2. Install Playwright browsers
3. Start the app with the Procfile command
4. Assign a public URL

**Deployment takes 3-5 minutes**

### Step 6: Get Your Deployment URL

In Railway Dashboard:
- Click your project
- Look for "Deployments" tab
- Find the active deployment
- Copy the URL (e.g., `https://omi-uber-app-production.up.railway.app`)

---

## Part 3: Testing on Railway

### Test 1: Health Check

```bash
curl https://YOUR_RAILWAY_URL/health
```

### Test 2: Home Page

```bash
curl https://YOUR_RAILWAY_URL/?uid=test_user
```

### Test 3: Authentication

1. Visit: `https://YOUR_RAILWAY_URL/auth?uid=test_user`
2. Complete authentication
3. Should redirect to home with "✅ Connected"

### Test 4: Webhook

```bash
curl -X POST https://YOUR_RAILWAY_URL/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "test_user",
    "segments": [{"text": "book an uber from downtown to the airport", "speaker": "user"}]
  }'
```

---

## Part 4: Integrate with Omi App

### Step 1: Get Your Railway URLs

You need these 4 URLs from your Railway deployment:

```
Base URL: https://YOUR_RAILWAY_URL

App Home URL:
https://YOUR_RAILWAY_URL/

Auth URL:
https://YOUR_RAILWAY_URL/auth

Setup Completed URL:
https://YOUR_RAILWAY_URL/setup-completed

Webhook URL:
https://YOUR_RAILWAY_URL/webhook
```

### Step 2: Configure in Omi App

In the Omi app settings:

1. **App Home URL**: `https://YOUR_RAILWAY_URL/`
2. **Auth URL**: `https://YOUR_RAILWAY_URL/auth`
3. **Setup Completed URL**: `https://YOUR_RAILWAY_URL/setup-completed`
4. **Webhook URL**: `https://YOUR_RAILWAY_URL/webhook`

### Step 3: Test on Omi Device

1. Open Omi app
2. Navigate to Uber integration
3. Click "Connect Uber Account"
4. Complete authentication (including 2FA if needed)
5. Should see "✅ Uber Connected"

### Step 4: Test Voice Commands

Say to your Omi device:

**Example 1**: "Book an Uber from downtown to the airport"
- Expected: Ride booked from downtown to airport

**Example 2**: "Get me a ride from my home to work"
- Expected: Ride booked from home to work

**Example 3**: "Call an Uber from the office to the station"
- Expected: Ride booked from office to station

---

## Voice Command Format

The app now supports **START → END** locations:

### Supported Phrases

```
"Book an Uber from [START] to [END]"
"Get me a ride from [START] to [END]"
"Call an Uber from [START] to [END]"
"Request an Uber from [START] to [END]"
"Order an Uber from [START] to [END]"
```

### Examples

```
"Book an Uber from downtown to the airport"
"Get me a ride from my house to the office"
"Call an Uber from the station to the mall"
"Request an Uber from home to work"
"Order an Uber from the hotel to the airport"
```

### Location Examples

- **Specific addresses**: "123 Main Street to 456 Oak Avenue"
- **Landmarks**: "downtown to the airport"
- **Neighborhoods**: "Mission District to Financial District"
- **Named places**: "home to work", "office to the gym"
- **Intersections**: "5th and Market to 3rd and Mission"

---

## Webhook Request/Response Format

### Request Format

```json
{
  "uid": "user123",
  "segments": [
    {
      "text": "book an uber from downtown to the airport",
      "speaker": "user"
    }
  ]
}
```

### Response Format (Success)

```json
{
  "message": "🚗 Booking Uber from downtown to the airport...",
  "booked": true,
  "start_location": "downtown",
  "end_location": "the airport"
}
```

### Response Format (Error)

```json
{
  "message": "⚠️ Please authenticate your Uber account first",
  "booked": false
}
```

---

## Troubleshooting

### Local Testing Issues

**"OPENAI_API_KEY not set"**
```bash
export OPENAI_API_KEY=sk-...
# Or edit .env file
```

**"Playwright not installed"**
```bash
playwright install chromium
```

**"Port 8000 already in use"**
```bash
uvicorn main:app --port 8001
```

### Railway Deployment Issues

**"Build failed"**
1. Check Railway logs: Click project → Deployments → View logs
2. Verify `requirements.txt` has all dependencies
3. Check `Procfile` syntax

**"App crashes after deployment"**
1. Check logs for errors
2. Verify OPENAI_API_KEY is set
3. Check if Playwright installation succeeded

**"Endpoints return 404"**
1. Verify Railway URL is correct
2. Check if app is running (green status in Railway)
3. Wait 1-2 minutes for deployment to fully initialize

### Omi Integration Issues

**"Omi can't reach the app"**
1. Verify Railway URL is correct
2. Test with curl: `curl https://YOUR_URL/health`
3. Check if app is running in Railway dashboard

**"Authentication fails"**
1. Verify Uber account is valid
2. Check browser console for errors
3. Try manual authentication first

**"2FA not detected"**
1. Verify 2FA is enabled on Uber account
2. Check if Uber UI has changed
3. Try re-authenticating

---

## Monitoring

### Check App Status

**Railway Dashboard**:
1. Go to https://railway.app
2. Click your project
3. Check "Deployments" tab
4. Green status = running ✅

### View Logs

**Railway Logs**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs
```

### Monitor Bookings

Check user data files:
```bash
# Local
cat users/user123.json

# On Railway (via SSH or file browser)
# Check sessions and users directories
```

---

## Performance Tips

1. **Reuse sessions**: App automatically saves and reuses sessions
2. **Headless mode**: Bookings run in headless mode (faster)
3. **Background tasks**: Booking happens in background (non-blocking)
4. **Caching**: Sessions cached to avoid re-login

---

## Security Checklist

- [ ] OPENAI_API_KEY set in Railway environment variables
- [ ] .env file NOT committed to git
- [ ] HTTPS used (Railway provides this)
- [ ] Rate limiting on 2FA endpoint
- [ ] Session files stored securely
- [ ] No sensitive data in logs

---

## Complete Testing Checklist

### Local Testing
- [ ] Health check works
- [ ] Home page loads
- [ ] Auth flow works
- [ ] 2FA code submission works
- [ ] Webhook accepts requests
- [ ] Tests pass: `pytest test_app.py -v`

### Railway Deployment
- [ ] Repository pushed to GitHub
- [ ] Railway project created
- [ ] OPENAI_API_KEY set
- [ ] Deployment successful (green status)
- [ ] Health check works on Railway URL
- [ ] Home page loads on Railway URL

### Omi Integration
- [ ] All 4 URLs configured in Omi app
- [ ] Authentication works on Omi
- [ ] 2FA works on Omi
- [ ] Voice command triggers booking
- [ ] Booking confirmation received

---

## Next Steps

1. ✅ Setup local environment
2. ✅ Test all endpoints locally
3. ✅ Deploy to Railway
4. ✅ Test on Railway
5. ✅ Configure in Omi app
6. ✅ Test voice commands on Omi device
7. ✅ Monitor and optimize

---

**Ready to test and deploy! 🚀**
