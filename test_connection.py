#!/usr/bin/env python3
import pymysql

# Get the password
password = "*gCI*R#(geZv=:S?c}lynS6Yegq-V>NK"

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        port=3308,
        user='acro_user',
        password=password,
        database='acro_planner',
        connect_timeout=10
    )
    
    print("✅ Connected successfully!")
    
    # Test query
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Test query result: {result}")
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'system_settings'")
        result = cursor.fetchone()
        if result:
            print("✅ system_settings table exists")
            
            # Count rows
            cursor.execute("SELECT COUNT(*) FROM system_settings")
            count = cursor.fetchone()[0]
            print(f"Number of rows in system_settings: {count}")
        else:
            print("❌ system_settings table does not exist")
    
    connection.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")