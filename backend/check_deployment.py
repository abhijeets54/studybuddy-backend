#!/usr/bin/env python
"""
Deployment readiness checker for StudyBuddy backend
Run this script to verify your deployment configuration
"""

import os
import sys
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

def check_file_exists(file_path, description):
    """Check if a file exists and print status"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False

def check_env_var(var_name, required=True):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        print(f"✅ Environment variable {var_name}: Set")
        return True
    else:
        status = "❌" if required else "⚠️"
        req_text = "REQUIRED" if required else "OPTIONAL"
        print(f"{status} Environment variable {var_name}: Not set ({req_text})")
        return not required

def main():
    print("🔍 StudyBuddy Backend Deployment Readiness Check")
    print("=" * 50)

    # Load environment variables from .env file
    load_env_file()
    
    all_good = True
    
    # Check required files
    print("\n📁 Checking required files...")
    files_to_check = [
        ("requirements.txt", "Python dependencies"),
        ("build.sh", "Build script"),
        ("Procfile", "Process file"),
        ("runtime.txt", "Python runtime"),
        ("manage.py", "Django management script"),
        ("studybuddy/settings.py", "Django settings"),
        ("studybuddy/wsgi.py", "WSGI application"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False
    
    # Check environment variables
    print("\n🔧 Checking environment variables...")
    env_vars = [
        ("SECRET_KEY", True),
        ("DATABASE_URL", True),
        ("GEMINI_API_KEY", True),
        ("DEBUG", False),
        ("ALLOWED_HOSTS", False),
        ("CORS_ALLOWED_ORIGINS", False),
    ]
    
    for var_name, required in env_vars:
        if not check_env_var(var_name, required):
            if required:
                all_good = False
    
    # Check .env file
    print("\n📄 Checking configuration files...")
    if check_file_exists(".env", "Environment file"):
        print("   Note: .env file should NOT be committed to version control")
    
    check_file_exists(".env.example", "Example environment file")
    check_file_exists(".gitignore", "Git ignore file")
    
    # Final status
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All checks passed! Your backend is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Create a Render account")
        print("3. Follow the DEPLOYMENT_GUIDE.md")
    else:
        print("⚠️  Some issues found. Please fix them before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
