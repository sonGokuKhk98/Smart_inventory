# 🚀 Deployment Guide - VisionFlow to Render

## Quick Deployment Checklist

### Pre-Deployment
- [ ] Code pushed to GitHub repository
- [ ] `render.yaml` file exists in root directory
- [ ] `backend/requirements.txt` is up to date
- [ ] `GEMINI_API_KEY` ready (don't commit to repo!)

### Deployment Steps

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub (recommended)

2. **Deploy via Blueprint (Easiest)**
   - Click "New +" → "Blueprint"
   - Connect GitHub repository
   - Render auto-detects `render.yaml`
   - Click "Apply"

3. **Set Environment Variables**
   - Go to service → Environment tab
   - Add: `GEMINI_API_KEY` = `your-api-key-here`
   - Save changes

4. **Monitor Deployment**
   - Watch build logs
   - Wait for "Live" status
   - Note your service URL: `https://your-service.onrender.com`

### Post-Deployment

1. **Test Your Deployment**
   ```bash
   # Test frontend
   curl https://your-service.onrender.com/
   
   # Test API docs
   curl https://your-service.onrender.com/docs
   
   # Test API endpoint
   curl https://your-service.onrender.com/openapi.json
   ```

2. **Update watsonx Orchestrate**
   - Get your Render URL
   - Update OpenAPI skill server URL in watsonx
   - Or use: `https://your-service.onrender.com/openapi.json`

3. **Verify Frontend Works**
   - Visit `https://your-service.onrender.com/`
   - Should see VisionFlow Logistics Hub
   - Test image upload functionality

## Configuration Files

### render.yaml
```yaml
services:
  - type: web
    name: visionflow-backend
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r backend/requirements.txt
    startCommand: python backend/main_supply_chain.py
    envVars:
      - key: GEMINI_API_KEY
        sync: false
    healthCheckPath: /docs
```

### Procfile (Alternative)
```
web: python backend/main_supply_chain.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for vision AI |
| `PORT` | Auto-set | Port number (automatically set by Render) |

## Troubleshooting

### Build Fails
- Check `backend/requirements.txt` exists
- Verify Python version compatibility
- Review build logs for specific errors

### Service Won't Start
- Verify `GEMINI_API_KEY` is set
- Check start command in render.yaml
- Review runtime logs

### Frontend Not Loading
- Verify `frontend/index.html` exists
- Check static file serving in `main_supply_chain.py`
- Test root route: `curl https://your-service.onrender.com/`

### API Calls Fail
- Check CORS configuration
- Verify backend is running
- Test API docs: `https://your-service.onrender.com/docs`

## Free Tier Limitations

- **Spin-down:** Service sleeps after 15 min inactivity
- **Cold Start:** First request after sleep takes 30-60 seconds
- **Upgrade:** Paid plans offer always-on service

## Support

- Render Docs: https://render.com/docs
- Render Status: https://status.render.com
- Project Issues: Create issue in GitHub repository

