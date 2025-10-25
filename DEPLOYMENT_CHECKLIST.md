# Deployment Checklist ✅

Complete checklist for deploying the Omi Uber App to production.

## Pre-Deployment Setup

### Local Development
- [ ] Clone repository
- [ ] Run `./setup.sh`
- [ ] Activate virtual environment: `source venv/bin/activate`
- [ ] Add OPENAI_API_KEY to `.env`
- [ ] Test locally: `uvicorn main:app --reload`
- [ ] Visit http://localhost:8000
- [ ] Run tests: `pytest test_app.py -v`

### Code Review
- [ ] Review all Python files for syntax errors
- [ ] Check for hardcoded secrets (should be in .env)
- [ ] Verify error handling is comprehensive
- [ ] Check logging doesn't expose sensitive data
- [ ] Review 2FA handling logic
- [ ] Verify session management is secure

### Testing
- [ ] Test home page loads
- [ ] Test authentication flow manually
- [ ] Test 2FA code submission
- [ ] Test webhook with valid trigger
- [ ] Test webhook without trigger
- [ ] Test error handling
- [ ] Test session validation
- [ ] Run full test suite: `pytest test_app.py -v`

---

## Deployment to Railway

### Step 1: Create Railway Account
- [ ] Go to https://railway.app
- [ ] Sign up with GitHub account
- [ ] Verify email
- [ ] Create new project

### Step 2: Prepare Repository
- [ ] Initialize git repository: `git init`
- [ ] Add all files: `git add .`
- [ ] Commit: `git commit -m "Initial commit"`
- [ ] Create GitHub repository
- [ ] Push to GitHub: `git push origin main`

### Step 3: Connect to Railway
- [ ] Install Railway CLI: `npm install -g @railway/cli`
- [ ] Login: `railway login`
- [ ] Link project: `railway link`
- [ ] Verify connection

### Step 4: Configure Environment
- [ ] Set OPENAI_API_KEY: `railway variables set OPENAI_API_KEY=your_key`
- [ ] Set PORT: `railway variables set PORT=8000`
- [ ] Verify variables: `railway variables`

### Step 5: Deploy
- [ ] Deploy: `railway up`
- [ ] Wait for build to complete
- [ ] Check deployment status in Railway dashboard
- [ ] Get deployment URL

### Step 6: Post-Deployment Tests
- [ ] Test health check: `curl https://your-app.railway.app/health`
- [ ] Test home page: `curl https://your-app.railway.app/`
- [ ] Test auth status: `curl https://your-app.railway.app/auth-status?uid=test`
- [ ] Check logs: `railway logs`
- [ ] Monitor for errors

---

## Deployment to Heroku

### Step 1: Create Heroku Account
- [ ] Go to https://heroku.com
- [ ] Sign up
- [ ] Verify email
- [ ] Create new app

### Step 2: Install Heroku CLI
- [ ] Install: `brew tap heroku/brew && brew install heroku`
- [ ] Login: `heroku login`
- [ ] Verify: `heroku --version`

### Step 3: Prepare Repository
- [ ] Initialize git: `git init`
- [ ] Add files: `git add .`
- [ ] Commit: `git commit -m "Initial commit"`
- [ ] Create GitHub repository
- [ ] Push to GitHub: `git push origin main`

### Step 4: Connect to Heroku
- [ ] Create app: `heroku create your-app-name`
- [ ] Verify: `heroku apps`

### Step 5: Configure Environment
- [ ] Set API key: `heroku config:set OPENAI_API_KEY=your_key`
- [ ] Verify: `heroku config`

### Step 6: Deploy
- [ ] Deploy: `git push heroku main`
- [ ] Wait for build to complete
- [ ] Check deployment: `heroku logs --tail`

### Step 7: Post-Deployment Tests
- [ ] Test health: `curl https://your-app-name.herokuapp.com/health`
- [ ] Test home: `curl https://your-app-name.herokuapp.com/`
- [ ] Monitor logs: `heroku logs --tail`

---

## Docker Deployment

### Step 1: Build Docker Image
- [ ] Build: `docker build -t omi-uber-app .`
- [ ] Verify: `docker images | grep omi-uber-app`

### Step 2: Test Locally
- [ ] Run: `docker run -p 8000:8000 -e OPENAI_API_KEY=your_key omi-uber-app`
- [ ] Test: `curl http://localhost:8000/health`
- [ ] Stop: `Ctrl+C`

### Step 3: Push to Registry
- [ ] Login to Docker Hub: `docker login`
- [ ] Tag: `docker tag omi-uber-app your-username/omi-uber-app`
- [ ] Push: `docker push your-username/omi-uber-app`

### Step 4: Deploy to Cloud
- [ ] Choose cloud provider (AWS, GCP, Azure, DigitalOcean, etc.)
- [ ] Create container service
- [ ] Set environment variables
- [ ] Deploy image
- [ ] Configure domain/URL
- [ ] Test endpoints

---

## Omi Integration Setup

### Step 1: Get Deployment URL
- [ ] From Railway: `https://your-project.railway.app`
- [ ] From Heroku: `https://your-app-name.herokuapp.com`
- [ ] From Docker: Your cloud provider URL

### Step 2: Configure URLs in Omi App
- [ ] App Home URL: `https://your-app.railway.app/`
- [ ] Auth URL: `https://your-app.railway.app/auth`
- [ ] Setup Completed URL: `https://your-app.railway.app/setup-completed`
- [ ] Webhook URL: `https://your-app.railway.app/webhook`

### Step 3: Test Integration
- [ ] Open Omi app
- [ ] Navigate to Uber integration
- [ ] Click "Connect Uber Account"
- [ ] Complete authentication
- [ ] Verify "✅ Uber Connected" message
- [ ] Test voice command: "Book an Uber to [destination]"

### Step 4: Monitor Integration
- [ ] Check app logs for errors
- [ ] Monitor webhook calls
- [ ] Track authentication success rate
- [ ] Monitor booking success rate

---

## Security Checklist

### Secrets Management
- [ ] OPENAI_API_KEY in environment variables (not in code)
- [ ] No hardcoded credentials in repository
- [ ] .env file in .gitignore
- [ ] .env.example has placeholder values only

### API Security
- [ ] HTTPS enforced in production
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] Error messages don't expose sensitive data
- [ ] Logging doesn't include sensitive data

### Data Protection
- [ ] Session files stored securely
- [ ] 2FA codes never logged
- [ ] User data encrypted at rest (if applicable)
- [ ] Database credentials in environment variables
- [ ] Regular backups configured

### Browser Automation
- [ ] Headless mode for bookings
- [ ] Visible mode only for authentication
- [ ] Playwright stealth plugin ready
- [ ] User-agent rotation possible
- [ ] No credentials stored in browser

---

## Performance Checklist

### Optimization
- [ ] Async/await used throughout
- [ ] Database queries optimized (if applicable)
- [ ] Caching configured
- [ ] CDN configured (if applicable)
- [ ] Image optimization done
- [ ] Minification enabled (if applicable)

### Monitoring
- [ ] Health check endpoint working
- [ ] Response times monitored
- [ ] Error rates tracked
- [ ] Database performance monitored
- [ ] API rate limits set

### Scaling
- [ ] Load balancing configured (if needed)
- [ ] Auto-scaling enabled
- [ ] Database replication set up (if needed)
- [ ] Cache cluster configured (if needed)
- [ ] CDN distribution configured (if needed)

---

## Monitoring & Logging

### Application Monitoring
- [ ] Health check endpoint: `/health`
- [ ] Error logging enabled
- [ ] Request logging enabled
- [ ] Performance metrics tracked
- [ ] Alerts configured

### Deployment Monitoring
- [ ] Railway dashboard monitored
- [ ] Heroku dashboard monitored
- [ ] Docker container health checked
- [ ] Uptime monitoring configured
- [ ] Error notifications enabled

### Logging
- [ ] Logs accessible and readable
- [ ] Log retention configured
- [ ] Log aggregation set up (if needed)
- [ ] Error alerts configured
- [ ] Debug logging available

---

## Post-Deployment Verification

### Endpoint Testing
- [ ] GET `/` - Home page loads
- [ ] GET `/health` - Health check works
- [ ] GET `/auth-status?uid=test` - Status endpoint works
- [ ] GET `/setup-completed?uid=test` - Setup check works
- [ ] POST `/webhook` - Webhook accepts requests

### Authentication Testing
- [ ] Manual authentication flow works
- [ ] 2FA detection works
- [ ] 2FA code submission works
- [ ] Session saved correctly
- [ ] Session validation works

### Booking Testing
- [ ] Trigger phrase detection works
- [ ] Destination extraction works
- [ ] Headless browser automation works
- [ ] Ride details extracted correctly
- [ ] Booking confirmation sent

### Error Handling
- [ ] Invalid input handled gracefully
- [ ] Missing environment variables handled
- [ ] Browser automation timeouts handled
- [ ] API errors handled
- [ ] User-friendly error messages shown

---

## Rollback Plan

### If Deployment Fails

#### Railway
- [ ] Check logs: `railway logs`
- [ ] Rollback to previous version: `railway rollback`
- [ ] Verify: `railway logs`

#### Heroku
- [ ] Check logs: `heroku logs --tail`
- [ ] Rollback: `heroku releases:rollback`
- [ ] Verify: `heroku logs --tail`

#### Docker
- [ ] Stop current container: `docker stop <container-id>`
- [ ] Run previous image: `docker run -p 8000:8000 <previous-image>`
- [ ] Verify: `curl http://localhost:8000/health`

### If Issues Occur
- [ ] Check application logs
- [ ] Verify environment variables
- [ ] Test endpoints manually
- [ ] Check external API availability
- [ ] Review recent code changes
- [ ] Rollback if necessary

---

## Maintenance

### Regular Tasks
- [ ] Monitor application logs daily
- [ ] Check error rates
- [ ] Review performance metrics
- [ ] Update dependencies monthly
- [ ] Backup user data regularly
- [ ] Test disaster recovery

### Updates
- [ ] Update Python packages: `pip install --upgrade -r requirements.txt`
- [ ] Update Playwright: `playwright install chromium`
- [ ] Update Docker image: `docker build --no-cache .`
- [ ] Test updates in staging first
- [ ] Deploy to production

### Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure error alerts
- [ ] Track performance metrics
- [ ] Monitor API usage
- [ ] Review user feedback

---

## Documentation

### Before Deployment
- [ ] README.md complete and accurate
- [ ] QUICKSTART.md tested
- [ ] OMI_INTEGRATION.md complete
- [ ] ARCHITECTURE.md up to date
- [ ] API documentation complete

### After Deployment
- [ ] Update deployment URLs in documentation
- [ ] Document any customizations
- [ ] Create runbook for common issues
- [ ] Document monitoring setup
- [ ] Create incident response plan

---

## Sign-Off

- [ ] All checklist items completed
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Security review completed
- [ ] Performance verified
- [ ] Documentation complete
- [ ] Team notified
- [ ] Ready for production

---

## Deployment Summary

**Deployment Date**: _______________

**Deployed By**: _______________

**Deployment URL**: _______________

**Issues Encountered**: _______________

**Resolution**: _______________

**Verified By**: _______________

---

**Deployment complete! 🚀**
