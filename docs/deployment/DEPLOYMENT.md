# Deployment Guide - Digital Ocean App Platform

This guide walks you through deploying the Cashflow Scheduler to Digital Ocean App Platform.

## Prerequisites

- [ ] Digital Ocean account ([Sign up here](https://www.digitalocean.com/))
- [ ] GitHub account with this repository
- [ ] Git repository pushed to GitHub

## Overview

Your application consists of two services:
1. **API Service**: FastAPI backend (Python) - runs the solver
2. **Web Service**: Next.js frontend (Node.js) - user interface

Both services will be deployed and managed by Digital Ocean App Platform.

## Step 1: Prepare Your Repository

### 1.1 Update the app.yaml Configuration

Open `.do/app.yaml` and replace:
```yaml
github:
  repo: YOUR_GITHUB_USERNAME/cashflow-scheduler
```

With your actual GitHub username:
```yaml
github:
  repo: yourusername/cashflow-scheduler  # Replace with your username
```

### 1.2 Commit and Push Changes

```bash
git add .
git commit -m "chore: add Digital Ocean deployment configuration"
git push origin main
```

## Step 2: Create App on Digital Ocean

### 2.1 Connect to App Platform

1. Go to [Digital Ocean Console](https://cloud.digitalocean.com/)
2. Click **Create** → **Apps**
3. Choose **GitHub** as your source
4. Click **Manage Access** and authorize Digital Ocean to access your repositories

### 2.2 Select Repository

1. Select your `cashflow-scheduler` repository
2. Select the `main` branch
3. Check **Autodeploy** (deploys automatically on git push)
4. Click **Next**

### 2.3 Configure Resources

Digital Ocean should detect your `app.yaml` and auto-configure. Verify:

**API Service:**
- Name: `api`
- Type: Dockerfile
- Dockerfile Path: `Dockerfile`
- HTTP Port: `8000`
- Instance Size: Basic (XXS) - $5/month
- Instance Count: 1

**Web Service:**
- Name: `web`
- Type: Node.js
- Build Command: `cd web && npm ci && npm run build`
- Run Command: `cd web && npm start`
- HTTP Port: `3000`
- Instance Size: Basic (XXS) - $5/month
- Instance Count: 1

Click **Next**.

### 2.4 Configure Environment Variables

**For API Service:**
Add these environment variables:
- `PYTHONPATH` = `/app`
- `PORT` = `8000`
- `CORS_ORIGINS` = `${web.PUBLIC_URL}` (this auto-references your frontend URL)

**For Web Service:**
Add these environment variables:
- `NODE_ENV` = `production`
- `NEXT_PUBLIC_API_URL` = `${api.PUBLIC_URL}` (this auto-references your API URL)

Click **Next**.

### 2.5 Review and Deploy

1. Review your app configuration
2. Choose your app name (e.g., `cashflow-scheduler`)
3. Select region closest to your users
4. Click **Create Resources**

## Step 3: Wait for Deployment

The first deployment takes 5-10 minutes. Digital Ocean will:
1. Clone your repository
2. Build Docker image for API service
3. Build Next.js application
4. Deploy both services
5. Provide public URLs

You can watch the build logs in real-time.

## Step 4: Access Your Application

Once deployed, you'll get URLs like:
- **Frontend**: `https://cashflow-scheduler-xxxxx.ondigitalocean.app`
- **API**: `https://cashflow-scheduler-api-xxxxx.ondigitalocean.app`

Click on the frontend URL to access your application!

## Step 5: Configure Custom Domain (Optional)

### 5.1 Add Domain

1. In App Platform dashboard, go to **Settings** → **Domains**
2. Click **Add Domain**
3. Enter your domain (e.g., `cashflow.yourdomain.com`)
4. Choose which service (probably `web`)
5. Click **Add Domain**

### 5.2 Update DNS Records

Add these DNS records at your domain registrar:

**For root domain (yourdomain.com):**
```
Type: A
Name: @
Value: [IP provided by Digital Ocean]
```

**For subdomain (cashflow.yourdomain.com):**
```
Type: CNAME
Name: cashflow
Value: [CNAME provided by Digital Ocean]
```

### 5.3 Update CORS Origins

Once your custom domain is set up:

1. Go to App Platform → `api` service → Settings
2. Add environment variable:
   - `CORS_ORIGINS` = `https://yourdomain.com,https://www.yourdomain.com`
3. Click **Save**
4. API will redeploy with new CORS settings

## Step 6: Monitor Your Application

### 6.1 View Logs

- Go to your app → Select service → **Runtime Logs**
- View real-time logs for debugging

### 6.2 Check Metrics

- Go to your app → **Insights**
- Monitor CPU, Memory, Request rates
- Set up alerts for high usage

### 6.3 Health Checks

Your API has a health endpoint:
```
https://your-api-url.ondigitalocean.app/health
```

Should return:
```json
{"status": "ok"}
```

## Troubleshooting

### Build Fails

**Problem**: Docker build fails for API
**Solution**: Check build logs. Most common issues:
- OR-Tools installation failing → Ensure Dockerfile has build tools (gcc, g++, make)
- Missing dependencies → Check requirements.txt

**Problem**: Next.js build fails
**Solution**:
- Check Node.js version compatibility
- Ensure all dependencies in package.json
- Check build logs for TypeScript errors

### Runtime Errors

**Problem**: API returns 500 errors
**Solution**:
1. Check Runtime Logs for API service
2. Verify PYTHONPATH is set to `/app`
3. Check if OR-Tools installed correctly

**Problem**: Frontend can't connect to API
**Solution**:
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check API health endpoint
3. Verify CORS_ORIGINS includes frontend URL
4. Check browser console for CORS errors

### Performance Issues

**Problem**: Solver is slow or timing out
**Solution**:
1. Upgrade API service to larger instance:
   - Basic-XS: $12/month (1 vCPU, 512MB)
   - Basic-S: $24/month (1 vCPU, 1GB)
2. Consider adding request timeout limits
3. Monitor solver performance in logs

## Updating Your Application

### Automatic Deployments

With autodeploy enabled:
```bash
# Make changes locally
git add .
git commit -m "feat: add new feature"
git push origin main

# Digital Ocean automatically deploys changes
```

### Manual Deployments

1. Go to App Platform dashboard
2. Click your app
3. Click **Deploy**
4. Select branch or commit
5. Click **Deploy**

## Cost Estimate

**Minimum Configuration:**
- API Service (Basic-XXS): $5/month
- Web Service (Basic-XXS): $5/month
- **Total: $10/month**

**Recommended Configuration:**
- API Service (Basic-XS): $12/month (better for solver)
- Web Service (Basic-XXS): $5/month
- **Total: $17/month**

**With Custom Domain:**
- Add $0/month (free with App Platform)

## Scaling

As your traffic grows:

1. **Horizontal Scaling**: Increase instance count
   - Settings → Scale → Increase to 2-3 instances
   - Load balanced automatically

2. **Vertical Scaling**: Upgrade instance size
   - Settings → Instance Size → Choose larger size
   - More CPU/RAM for solver performance

3. **Add CDN**: Digital Ocean Spaces + CDN
   - Cache static assets
   - Reduce frontend load times

## Security Recommendations

1. **Enable HTTPS** (automatic with App Platform)
2. **Restrict CORS origins** (already configured)
3. **Add rate limiting** (consider adding middleware)
4. **Monitor logs** for suspicious activity
5. **Keep dependencies updated**:
   ```bash
   cd web && npm audit fix
   pip list --outdated
   ```

## Backup and Disaster Recovery

**App Configuration Backup:**
Your `app.yaml` is version controlled - safe in git!

**Database Backup** (if you add one later):
- App Platform → Database → Settings → Automated Backups
- Daily backups retained for 7 days

**Code Backup:**
- Push to GitHub regularly
- Consider GitLab or Bitbucket as backup remote

## Support

- [Digital Ocean Documentation](https://docs.digitalocean.com/products/app-platform/)
- [Digital Ocean Community](https://www.digitalocean.com/community)
- [Support Tickets](https://cloud.digitalocean.com/support/tickets)

## Next Steps

- [ ] Deploy to Digital Ocean
- [ ] Test all functionality
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring alerts
- [ ] Share with users!

---

**Congratulations!** Your Cashflow Scheduler is now live and accessible to anyone with the URL.
