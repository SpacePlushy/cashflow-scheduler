# Pre-Deployment Checklist

Use this checklist before deploying to Digital Ocean.

## Code Preparation

- [ ] All tests passing: `cd cashflow && pytest`
- [ ] Web builds successfully: `cd web && npm run build`
- [ ] No TypeScript errors: `cd web && npm run lint`
- [ ] All changes committed to git
- [ ] Pushed to GitHub main branch

## Configuration Files

- [ ] `Dockerfile` exists in project root
- [ ] `.dockerignore` configured properly
- [ ] `.do/app.yaml` exists with correct GitHub repo name
- [ ] `web/.env.production.example` exists
- [ ] API CORS updated to use environment variable

## Repository Setup

- [ ] Repository is public or Digital Ocean has access
- [ ] Main branch is up to date
- [ ] No sensitive data committed (API keys, passwords, etc.)
- [ ] `requirements.txt` includes all Python dependencies
- [ ] `web/package.json` includes all Node dependencies

## Account Setup

- [ ] Digital Ocean account created
- [ ] GitHub account connected to Digital Ocean
- [ ] Payment method added (for billing)

## First Deployment

- [ ] Read `DEPLOYMENT.md` completely
- [ ] App created on Digital Ocean App Platform
- [ ] Both services (api and web) configured
- [ ] Environment variables set correctly
- [ ] Deployment initiated

## Post-Deployment

- [ ] API health check works: `https://your-api.ondigitalocean.app/health`
- [ ] Frontend loads correctly
- [ ] Can solve a schedule successfully
- [ ] Set EOD functionality works
- [ ] Validation checks display correctly
- [ ] Collapsible sections work
- [ ] Dark mode theme displays correctly
- [ ] Calendar tooltips work properly

## Optional (After Initial Deploy)

- [ ] Custom domain configured
- [ ] DNS records updated
- [ ] HTTPS certificate active (automatic)
- [ ] CORS origins updated for custom domain
- [ ] Monitoring alerts configured
- [ ] Performance testing completed

## Common Issues to Check

- [ ] OR-Tools installs correctly in Docker
- [ ] Frontend can reach API endpoint
- [ ] CORS headers allow frontend domain
- [ ] Environment variables are set
- [ ] Build logs show no errors
- [ ] Runtime logs show no errors

---

**Status**: ☐ Ready to Deploy | ☐ Deployed | ☐ Production Ready
