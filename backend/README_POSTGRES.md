# StudyBuddy Backend - PostgreSQL Setup

This guide will help you set up and run the StudyBuddy backend with PostgreSQL.

## Prerequisites

1. **PostgreSQL installed and running**
   - Download from: https://www.postgresql.org/download/
   - Make sure PostgreSQL service is running
   - Note your PostgreSQL admin password (usually for 'postgres' user)

2. **Python 3.8+ with pip**

## Setup Instructions

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Your `.env` file is already configured with PostgreSQL:
```
DATABASE_URL=postgresql://studybuddy_user:studybuddy_pass@localhost:5432/studybuddy_db
```

### 5. Set Up PostgreSQL Database
Run the setup script to create the database and user:
```bash
python setup_postgres.py
```

This script will:
- Create the `studybuddy_user` user
- Create the `studybuddy_db` database
- Grant necessary privileges
- Test the connection

### 6. Run Database Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 8. Start the Development Server
```bash
python manage.py runserver
```

The server will be available at: http://127.0.0.1:8000/

## Troubleshooting

### PostgreSQL Connection Issues
1. **Service not running**: Make sure PostgreSQL service is started
2. **Wrong password**: Verify your PostgreSQL admin password
3. **Port conflicts**: Default port is 5432, check if it's available

### Test Database Connection
```bash
python setup_postgres.py test
```

### Reset Database (if needed)
If you need to start fresh:
```bash
# Drop and recreate database (run in PostgreSQL admin console)
DROP DATABASE studybuddy_db;
DROP USER studybuddy_user;

# Then run setup again
python setup_postgres.py
python manage.py migrate
```

### Common Commands
```bash
# Check database status
python manage.py dbshell

# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Collect static files (for production)
python manage.py collectstatic
```

## Database Configuration Details

The application uses:
- **Database**: PostgreSQL
- **Connection pooling**: Enabled with `conn_max_age=600`
- **Health checks**: Enabled for connection reliability
- **Environment-based config**: Uses `python-decouple` for settings

## API Endpoints

Once running, you can access:
- **Admin panel**: http://127.0.0.1:8000/admin/
- **API root**: http://127.0.0.1:8000/api/
- **API documentation**: Check your Django REST framework browsable API

## Production Notes

For production deployment:
1. Set `DEBUG=False` in `.env`
2. Update `ALLOWED_HOSTS` with your domain
3. Use a production-grade PostgreSQL instance
4. Configure proper SSL/TLS
5. Use environment variables for sensitive data
