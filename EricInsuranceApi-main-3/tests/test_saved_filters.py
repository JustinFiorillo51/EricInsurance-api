#!/usr/bin/env python3
"""
Test script for Saved Filters functionality
This script tests the database connection and basic CRUD operations
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Session as DBSession
from sqlalchemy import text

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        with DBSession() as session:
            result = session.execute(text("SELECT 1 as test"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_saved_filters_table():
    """Test if the SavedFilters table exists"""
    try:
        with DBSession() as session:
            result = session.execute(text("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'SavedFilters'
            """))
            count = result.scalar()
            if count > 0:
                print("✅ SavedFilters table exists")
                return True
            else:
                print("❌ SavedFilters table does not exist")
                return False
    except Exception as e:
        print(f"❌ Error checking SavedFilters table: {e}")
        return False

def test_table_structure():
    """Test the table structure"""
    try:
        with DBSession() as session:
            result = session.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'SavedFilters'
                ORDER BY ORDINAL_POSITION
            """))
            columns = result.fetchall()
            
            expected_columns = [
                ('Filter_ID', 'int', 'NO'),
                ('Filter_Name', 'nvarchar', 'NO'),
                ('Filter_Configuration', 'ntext', 'NO'),
                ('User_ID', 'nvarchar', 'NO'),
                ('Created_Date', 'datetime2', 'NO'),
                ('LastModified_Date', 'datetime2', 'NO'),
                ('Is_Active', 'bit', 'NO')
            ]
            
            print("📋 Table structure:")
            for col in columns:
                print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} ({'NULL' if col.IS_NULLABLE == 'YES' else 'NOT NULL'})")
            
            if len(columns) == len(expected_columns):
                print("✅ Table structure matches expected schema")
                return True
            else:
                print("❌ Table structure does not match expected schema")
                return False
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return False

def test_sample_data():
    """Test inserting and retrieving sample data"""
    try:
        with DBSession() as session:
            # Sample filter data
            sample_filter = {
                "name": "Test Filter",
                "groups": [{
                    "id": 1,
                    "logicOperator": "AND",
                    "conditions": [{
                        "id": 1,
                        "field": "Name",
                        "operator": "contains",
                        "value": "test",
                        "value2": "",
                        "enabled": True,
                        "conditionLogicOperator": "AND"
                    }]
                }]
            }
            
            # Insert test data
            session.execute(text("""
                INSERT INTO dbo.SavedFilters (Filter_Name, Filter_Configuration, User_ID, Created_Date, LastModified_Date, Is_Active)
                VALUES (:filter_name, :filter_configuration, :user_id, GETUTCDATE(), GETUTCDATE(), 1)
            """), {
                'filter_name': sample_filter['name'],
                'filter_configuration': json.dumps(sample_filter['groups']),
                'user_id': 'TEST_USER'
            })
            
            # Retrieve test data
            result = session.execute(text("""
                SELECT Filter_ID, Filter_Name, Filter_Configuration, User_ID
                FROM dbo.SavedFilters 
                WHERE User_ID = 'TEST_USER' AND Filter_Name = 'Test Filter'
            """))
            
            row = result.first()
            if row:
                print("✅ Sample data inserted and retrieved successfully")
                
                # Clean up test data
                session.execute(text("""
                    DELETE FROM dbo.SavedFilters 
                    WHERE User_ID = 'TEST_USER' AND Filter_Name = 'Test Filter'
                """))
                print("✅ Test data cleaned up")
                return True
            else:
                print("❌ Failed to retrieve test data")
                return False
                
    except Exception as e:
        print(f"❌ Error testing sample data: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Saved Filters Database Implementation")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("SavedFilters Table Exists", test_saved_filters_table),
        ("Table Structure", test_table_structure),
        ("Sample Data Operations", test_sample_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Saved Filters database implementation is ready.")
    else:
        print("⚠️  Some tests failed. Please check the database setup.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 