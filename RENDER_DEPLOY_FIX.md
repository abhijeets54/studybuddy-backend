# 🔧 Render Deployment Fix for pkg_resources Error

## Problem
Getting `ModuleNotFoundError: No module named 'pkg_resources'` when deploying to Render.

## Root Cause
- Python 3.13 doesn't include `setuptools` by default
- `djangorestframework-simplejwt` depends on `pkg_resources` from `setuptools`

## ✅ Solution Applied

### 1. Fixed requirements.txt
Added `setuptools>=65.0.0` to requirements.txt

### 2. Updated build.sh
Added setuptools force reinstall:
```bash
pip install --upgrade pip
pip install --force-reinstall -U setuptools
```

### 3. Set Python Version
Using Python 3.11.9 in `runtime.txt` for better compatibility

## 🚀 Deploy Steps

1. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "Fix pkg_resources error for Render deployment"
   git push origin main
   ```

2. **In Render Dashboard:**
   - Go to your web service
   - Click "Manual Deploy" → "Clear build cache & deploy"

## 📋 Environment Variables Needed

Set these in Render dashboard:
```
SECRET_KEY=your-new-production-secret-key
DEBUG=False
DATABASE_URL=[From Database: your-postgres-db]
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
GEMINI_API_KEY=AIzaSyAopY0mr-N3dY01V7ReDIcQ8kHBRAsefOU
```

## 🎯 Build Configuration

- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn studybuddy.wsgi:application`
- **Python Version**: 3.11.9 (from runtime.txt)

This fix resolves the pkg_resources issue and ensures successful deployment! 🎉
