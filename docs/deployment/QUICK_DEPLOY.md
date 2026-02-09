# Quick Deploy Guide - 5 Minutes to Production

Get your Cashflow Scheduler live in 5 minutes!

## Prerequisites
- Digital Ocean account
- GitHub account with this repo

## Steps

### 1. Update Configuration (1 minute)

Edit `.do/app.yaml` line 13:
```yaml
repo: YOUR_GITHUB_USERNAME/cashflow-scheduler
```
Replace with your GitHub username.

### 2. Push to GitHub (1 minute)

```bash
git add .
git commit -m "feat: ready for deployment"
git push origin main
```

### 3. Create App on Digital Ocean (3 minutes)

1. Go to https://cloud.digitalocean.com/apps/new
2. Connect GitHub → Select your repository → Branch: `main`
3. Click **Next** (auto-detects app.yaml)
4. Verify configuration:
   - API service: Dockerfile, port 8000
   - Web service: Next.js, port 3000
5. Click **Next** → Review → **Create Resources**

### 4. Wait for Build

⏱️ First deployment: ~5-10 minutes

Watch the build logs while it deploys.

### 5. Access Your App

You'll get URLs like:
- Frontend: `https://your-app.ondigitalocean.app`
- API: `https://your-app-api.ondigitalocean.app`

Click the frontend URL - **you're live!** 🎉

## What's Deployed?

✅ FastAPI backend with Python solver (OR-Tools)
✅ Next.js frontend with dark purple theme
✅ Set EOD balance functionality
✅ Collapsible sections
✅ 30-day calendar with tooltips
✅ Auto-deployed on git push
✅ HTTPS enabled automatically
✅ CORS configured

## Cost

💰 **$10/month** (minimum)
- API: $5/month (Basic-XXS)
- Web: $5/month (Basic-XXS)

Upgrade to Basic-XS ($12) for API if solver is slow.

## Next Steps

- ✏️ See `DEPLOYMENT.md` for detailed guide
- 📋 Use `DEPLOYMENT_CHECKLIST.md` before deploying
- 🌐 Add custom domain (optional)
- 📊 Monitor in App Platform dashboard

## Troubleshooting

**Build fails?** → Check build logs in Digital Ocean console
**API not connecting?** → Verify `NEXT_PUBLIC_API_URL` environment variable
**CORS errors?** → Check `CORS_ORIGINS` includes your frontend URL

## Support

Need help? Check `DEPLOYMENT.md` for detailed troubleshooting.

---

**That's it!** Your Cashflow Scheduler is now live and accessible worldwide.
