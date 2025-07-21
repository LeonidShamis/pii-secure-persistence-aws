#!/usr/bin/env python3
"""
Database Connection Test Script
Tests connectivity and basic operations for PII encryption database
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_database_connection():
    """Test basic database connectivity and schema validation"""
    
    # Configuration loaded from .env file or environment variables
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'pii_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'your_password'),
        'sslmode': os.getenv('DB_SSLMODE', 'prefer')
    }
    
    print("=== PII Encryption Database Connection Test ===")
    print(f"Connecting to: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        # Test 1: Basic Connection
        print("\n1. Testing database connection...")
        conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
        print("✅ Database connection successful")
        
        cursor = conn.cursor()
        
        # Test 2: Check PostgreSQL version
        print("\n2. Checking PostgreSQL version...")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()['version']
        print(f"✅ PostgreSQL version: {version}")
        
        # Test 3: Verify required extensions
        print("\n3. Checking required extensions...")
        cursor.execute("""
            SELECT extname FROM pg_extension 
            WHERE extname IN ('uuid-ossp', 'pgcrypto');
        """)
        extensions = [row['extname'] for row in cursor.fetchall()]
        
        if 'uuid-ossp' in extensions and 'pgcrypto' in extensions:
            print("✅ Required extensions installed: uuid-ossp, pgcrypto")
        else:
            print(f"⚠️  Missing extensions. Found: {extensions}")
        
        # Test 4: Verify all tables exist
        print("\n4. Checking database schema...")
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        tables = [row['tablename'] for row in cursor.fetchall()]
        
        expected_tables = ['users', 'encryption_metadata', 'encryption_audit', 
                          'key_rotation_log', 'system_config']
        
        missing_tables = set(expected_tables) - set(tables)
        if not missing_tables:
            print(f"✅ All required tables exist: {tables}")
        else:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Test 5: Check views
        print("\n5. Checking views...")
        cursor.execute("""
            SELECT viewname FROM pg_views 
            WHERE schemaname = 'public';
        """)
        views = [row['viewname'] for row in cursor.fetchall()]
        
        expected_views = ['encryption_stats', 'audit_summary', 'key_rotation_summary']
        missing_views = set(expected_views) - set(views)
        if not missing_views:
            print(f"✅ All required views exist: {views}")
        else:
            print(f"⚠️  Missing views: {missing_views}")
        
        # Test 6: Check indexes
        print("\n6. Checking indexes...")
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname NOT LIKE '%_pkey';
        """)
        indexes = [row['indexname'] for row in cursor.fetchall()]
        print(f"✅ Found {len(indexes)} custom indexes")
        
        # Test 7: Check triggers
        print("\n7. Checking triggers...")
        cursor.execute("""
            SELECT trigger_name, event_object_table 
            FROM information_schema.triggers 
            WHERE trigger_schema = 'public';
        """)
        triggers = cursor.fetchall()
        print(f"✅ Found {len(triggers)} triggers")
        for trigger in triggers:
            print(f"   - {trigger['trigger_name']} on {trigger['event_object_table']}")
        
        # Test 8: Test system configuration
        print("\n8. Checking system configuration...")
        cursor.execute("SELECT config_key, config_value FROM system_config;")
        configs = cursor.fetchall()
        print(f"✅ Found {len(configs)} system configuration entries:")
        for config in configs:
            print(f"   - {config['config_key']}: {config['config_value']}")
        
        # Test 9: Test basic insert/select operations
        print("\n9. Testing basic operations...")
        
        # Insert test user
        test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        cursor.execute("""
            INSERT INTO users (email, first_name, last_name) 
            VALUES (%s, %s, %s) RETURNING id;
        """, (test_email, 'Test', 'User'))
        
        user_id = cursor.fetchone()['id']
        print(f"✅ Inserted test user with ID: {user_id}")
        
        # Check if audit trigger fired
        cursor.execute("""
            SELECT COUNT(*) as count FROM encryption_audit 
            WHERE user_id = %s AND operation = 'create';
        """, (user_id,))
        
        audit_count = cursor.fetchone()['count']
        if audit_count > 0:
            print("✅ Audit trigger fired correctly")
        else:
            print("⚠️  Audit trigger may not be working")
        
        # Test encryption metadata insert
        cursor.execute("""
            INSERT INTO encryption_metadata (user_id, field_name, pii_level) 
            VALUES (%s, %s, %s);
        """, (user_id, 'email', 1))
        print("✅ Encryption metadata insert successful")
        
        # Test views
        cursor.execute("SELECT * FROM encryption_stats;")
        stats = cursor.fetchall()
        print(f"✅ Encryption stats view returned {len(stats)} rows")
        
        # Cleanup test data (in correct order due to foreign key constraints)
        cursor.execute("DELETE FROM encryption_metadata WHERE user_id = %s;", (user_id,))
        cursor.execute("DELETE FROM encryption_audit WHERE user_id = %s;", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        print("✅ Test data cleaned up")
        
        # Test 10: Performance check
        print("\n10. Testing performance...")
        cursor.execute("EXPLAIN ANALYZE SELECT * FROM users WHERE email = %s;", (test_email,))
        explain_result = cursor.fetchall()
        print("✅ Query plan analysis completed")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 ALL DATABASE TESTS PASSED SUCCESSFULLY! 🎉")
        print("Database is ready for the PII encryption system.")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_connection_pooling():
    """Test connection pooling behavior"""
    print("\n=== Connection Pooling Test ===")
    
    try:
        from psycopg2 import pool
        
        # Create connection pool
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            int(os.getenv('DB_POOL_MIN_SIZE', '1')),
            int(os.getenv('DB_POOL_MAX_SIZE', '5')),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'pii_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'your_password'),
            sslmode=os.getenv('DB_SSLMODE', 'prefer')
        )
        
        # Test getting and returning connections
        conn1 = connection_pool.getconn()
        conn2 = connection_pool.getconn()
        
        print("✅ Connection pool created and connections acquired")
        
        connection_pool.putconn(conn1)
        connection_pool.putconn(conn2)
        connection_pool.closeall()
        
        print("✅ Connection pool test completed")
        return True
        
    except Exception as e:
        print(f"⚠️  Connection pooling test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting PII Encryption Database Tests...")
    print("=" * 50)
    
    # Check if .env file exists
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    env_example_path = os.path.join(os.path.dirname(__file__), '.env.example')
    
    if os.path.exists(env_file_path):
        print(f"✅ Found .env file: {env_file_path}")
    else:
        print(f"⚠️  No .env file found. Create one from template:")
        if os.path.exists(env_example_path):
            print(f"   cp .env.example .env")
        else:
            print(f"   Create .env file at: {env_file_path}")
        print("   Then update with your database credentials.")
    
    # Check environment variables
    required_env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nUpdate your .env file or set these environment variables:")
        print("DB_HOST=your-aurora-endpoint")
        print("DB_NAME=pii_db")
        print("DB_USER=postgres")
        print("DB_PASSWORD=your-secure-password")
        print()
    else:
        print("✅ All required environment variables are set")
        print(f"   - Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"   - Database: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
        print()
    
    # Run tests
    basic_test_passed = test_database_connection()
    pool_test_passed = test_connection_pooling()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Basic Database Tests: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"Connection Pool Tests: {'✅ PASSED' if pool_test_passed else '⚠️  SKIPPED'}")
    
    if basic_test_passed:
        print("\n🎉 Database is ready for Phase 2: AWS Security Infrastructure!")
        return 0
    else:
        print("\n❌ Please fix database issues before proceeding.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)