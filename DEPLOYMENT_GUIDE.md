# StudyBuddy Backend Deployment Guide for Render

## 🚀 Quick Deploy to Render

### Option 1: Using Render Dashboard (Recommended)

1. **Create a Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Create a PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Name: `studybuddy-db`
   - Database Name: `studybuddy_db`
   - User: `studybuddy_user`
   - Plan: Free
   - Click "Create Database"
   - **Save the connection string** (you'll need it)

3. **Deploy the Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing this backend
   - Configure:
     - **Name**: `studybuddy-backend`
     - **Runtime**: Python 3
     - **Build Command**: `./build.sh`
     - **Start Command**: `gunicorn studybuddy.wsgi:application`
     - **Plan**: Free

4. **Set Environment Variables**
   Add these in the "Environment" section:
   ```
   DATABASE_URL=<your-postgres-connection-string>
   SECRET_KEY=<generate-a-secure-secret-key>
   DEBUG=False
   ALLOWED_HOSTS=*
   CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
   GEMINI_API_KEY=<your-gemini-api-key>
   ```

### Option 2: Using render.yaml (Infrastructure as Code)

1. Update the `render.yaml` file with your frontend domain
2. Push to GitHub
3. In Render dashboard, click "New +" → "Blueprint"
4. Connect your repository and select `render.yaml`

## 🔧 Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Django secret key (generate new for production) | `your-super-secret-key-here` |
| `DEBUG` | Debug mode (always False in production) | `False` |
| `ALLOWED_HOSTS` | Allowed hostnames | `*` or `your-app.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Frontend domains | `https://your-frontend.com` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |

## 🔐 Security Notes

- Never commit your `.env` file to version control
- Generate a new `SECRET_KEY` for production
- Set `DEBUG=False` in production
- Use specific domains in `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` for production

## 📝 Post-Deployment Steps

1. **Test the API**
   - Visit `https://your-app.onrender.com/admin/` to verify deployment
   - Check API endpoints: `https://your-app.onrender.com/api/`

2. **Create Superuser** (if needed)
   - In Render dashboard, go to your service
   - Open "Shell" tab
   - Run: `python manage.py createsuperuser`

3. **Update Frontend**
   - Update your frontend's API base URL to point to your Render deployment
   - Update CORS settings with your frontend domain

## 🐛 Troubleshooting

### Common Issues:

1. **Build Fails**
   - Check build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`

2. **Database Connection Error**
   - Verify `DATABASE_URL` is correctly set
   - Ensure PostgreSQL database is created and running

3. **Static Files Not Loading**
   - Verify `whitenoise` is in `requirements.txt`
   - Check `STATIC_ROOT` and `STATICFILES_STORAGE` settings

4. **CORS Errors**
   - Update `CORS_ALLOWED_ORIGINS` with your frontend domain
   - Ensure frontend is using HTTPS in production

## 📊 Free Tier Limitations

- **Render Free Tier**:
  - 750 hours/month
  - 512MB RAM
  - Sleeps after 15 minutes of inactivity
  - 100GB bandwidth/month

- **PostgreSQL Free Tier**:
  - 1GB storage
  - 97 hours/month uptime
  - Shared CPU

## 🔄 Continuous Deployment

Your app will automatically redeploy when you push to your main branch on GitHub.

## 📞 Support

If you encounter issues:
1. Check Render's documentation: [render.com/docs](https://render.com/docs)
2. Review build and runtime logs in Render dashboard
3. Ensure all environment variables are properly set
