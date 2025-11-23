# 🔧 Render Manual Setup Instructions

If you're setting up manually (not using Blueprint), use these exact values:

## Form Fields

### Branch
- **Value:** `main` (or your default branch)

### Region
- **Value:** `Oregon (US West)` (or your preferred region)

### Root Directory (Optional)
- **Value:** Leave **EMPTY** (don't fill this)

### Build Command
- **Value:** `pip install -r backend/requirements.txt`
- **NOT:** `pip install -r requirements.txt` ❌

### Start Command
- **Value:** `python backend/main_supply_chain.py`
- **NOT:** `gunicorn your_application.wsgi` ❌
- **NOT:** `uvicorn main:app` ❌

### Instance Type
- **Value:** `Free` (for testing) or upgrade for production

## Environment Variables

After creating the service, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Your Google Gemini API key |

## Quick Copy-Paste Commands

**Build Command:**
```
pip install -r backend/requirements.txt
```

**Start Command:**
```
python backend/main_supply_chain.py
```

## Why These Commands?

1. **Build Command:** Installs Python dependencies from `backend/requirements.txt`
2. **Start Command:** Runs the FastAPI application using Python directly (uvicorn is called inside the script)
3. **Root Directory:** Empty because our project structure has `backend/` as a subdirectory

## Alternative: Use Blueprint (Easier)

Instead of manual setup, use the Blueprint method:

1. Click "New +" → "Blueprint"
2. Connect your GitHub repo
3. Render will auto-detect `render.yaml`
4. Just add `GEMINI_API_KEY` environment variable
5. Deploy!

This is easier and less error-prone.

