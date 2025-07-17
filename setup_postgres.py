#!/usr/bin/env python
"""
PostgreSQL Database Setup Script for StudyBuddy

This script helps set up the PostgreSQL database for the StudyBuddy application.
It creates the database and user if they don't exist.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from decouple import config

def create_database():
    """Create PostgreSQL database and user if they don't exist."""
    
    # Database configuration from .env
    db_url = config('DATABASE_URL')
    
    # Parse the DATABASE_URL
    # Format: postgresql://username:password@host:port/database
    if not db_url.startswith('postgresql://'):
        print("❌ DATABASE_URL must start with 'postgresql://'")
        return False
    
    # Extract components
    url_parts = db_url.replace('postgresql://', '').split('/')
    db_name = url_parts[1] if len(url_parts) > 1 else 'studybuddy_db'
    
    auth_host = url_parts[0].split('@')
    host_port = auth_host[1] if len(auth_host) > 1 else 'localhost:5432'
    host = host_port.split(':')[0]
    port = host_port.split(':')[1] if ':' in host_port else '5432'
    
    if len(auth_host) > 1:
        user_pass = auth_host[0].split(':')
        username = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
    else:
        username = 'studybuddy_user'
        password = 'studybuddy_pass'
    
    print(f"🔧 Setting up PostgreSQL database:")
    print(f"   Host: {host}:{port}")
    print(f"   Database: {db_name}")
    print(f"   User: {username}")
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        print("\n📡 Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user='postgres',  # Default admin user
            password=input("Enter PostgreSQL admin password (usually for 'postgres' user): ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user if it doesn't exist
        print(f"👤 Creating user '{username}'...")
        try:
            cursor.execute(f"CREATE USER {username} WITH PASSWORD '{password}';")
            print(f"✅ User '{username}' created successfully")
        except psycopg2.errors.DuplicateObject:
            print(f"ℹ️  User '{username}' already exists")
        
        # Create database if it doesn't exist
        print(f"🗄️  Creating database '{db_name}'...")
        try:
            cursor.execute(f"CREATE DATABASE {db_name} OWNER {username};")
            print(f"✅ Database '{db_name}' created successfully")
        except psycopg2.errors.DuplicateDatabase:
            print(f"ℹ️  Database '{db_name}' already exists")
        
        # Grant privileges
        print(f"🔑 Granting privileges to '{username}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username};")
        cursor.execute(f"ALTER USER {username} CREATEDB;")
        
        cursor.close()
        conn.close()
        
        print("\n✅ PostgreSQL setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python manage.py migrate")
        print("2. Run: python manage.py createsuperuser")
        print("3. Run: python manage.py runserver")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Check if the admin password is correct")
        print("3. Verify PostgreSQL is accepting connections")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_connection():
    """Test connection to the configured database."""
    try:
        db_url = config('DATABASE_URL')
        print(f"🧪 Testing connection to database...")
        
        # Parse DATABASE_URL for connection
        import dj_database_url
        db_config = dj_database_url.parse(db_url)
        
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL version: {version[0]}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 StudyBuddy PostgreSQL Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_connection()
    else:
        if create_database():
            print("\n" + "=" * 40)
            test_connection()
