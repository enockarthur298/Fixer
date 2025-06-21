"""
Setup script for Basic Tech schema to store user context data.

This script helps create the necessary table structure in your Basic Tech project
for storing user interaction context in Fixer AI.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASIC_TECH_API_KEY = os.environ.get('BASIC_TECH_API_KEY', '')
BASIC_TECH_PROJECT_ID = os.environ.get('BASIC_TECH_PROJECT_ID', '')

def create_user_context_table():
    """Create the user_context table in Basic Tech project."""
    
    if not BASIC_TECH_API_KEY or not BASIC_TECH_PROJECT_ID:
        print("❌ Basic Tech API key or project ID not found in environment variables.")
        print("Please set BASIC_TECH_API_KEY and BASIC_TECH_PROJECT_ID in your .env file.")
        return False
    
    # Schema for user context table
    schema = {
        "tables": {
            "user_context": {
                "fields": {
                    "interactions": {
                        "type": "json",
                        "description": "Array of user interactions with timestamps and data"
                    },
                    "preferences": {
                        "type": "json", 
                        "description": "User preferences and settings"
                    },
                    "device_info": {
                        "type": "json",
                        "description": "User's device and system information"
                    },
                    "last_updated": {
                        "type": "string",
                        "description": "Timestamp of last context update"
                    }
                }
            }
        }
    }
    
    headers = {
        'Authorization': f'Bearer {BASIC_TECH_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Note: The exact endpoint for schema creation might vary
    # You may need to create this table through the Basic Tech admin portal
    # at https://app.basic.tech instead of via API
    
    print("🔧 Setting up Basic Tech schema for Fixer AI...")
    print(f"📋 Project ID: {BASIC_TECH_PROJECT_ID}")
    print(f"📊 Table: user_context")
    print("\n📝 Schema to create:")
    print(json.dumps(schema, indent=2))
    
    print("\n⚠️  IMPORTANT:")
    print("1. Go to https://app.basic.tech")
    print("2. Select your project")
    print("3. Create a new table called 'user_context'")
    print("4. Add the following fields:")
    print("   - interactions (type: json)")
    print("   - preferences (type: json)")
    print("   - device_info (type: json)")
    print("   - last_updated (type: string)")
    print("5. Publish your changes")
    
    return True

def test_basic_tech_connection():
    """Test connection to Basic Tech API."""
    
    if not BASIC_TECH_API_KEY or not BASIC_TECH_PROJECT_ID:
        print("❌ Basic Tech credentials not found.")
        return False
    
    headers = {
        'Authorization': f'Bearer {BASIC_TECH_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test project access
        url = f"https://api.basic.tech/project/{BASIC_TECH_PROJECT_ID}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Successfully connected to Basic Tech API!")
            print(f"📋 Project: {response.json().get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to connect to Basic Tech API: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Basic Tech API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Basic Tech Setup for Fixer AI")
    print("=" * 40)
    
    # Test connection first
    if test_basic_tech_connection():
        create_user_context_table()
    else:
        print("\n💡 Troubleshooting:")
        print("1. Verify your BASIC_TECH_API_KEY is correct")
        print("2. Verify your BASIC_TECH_PROJECT_ID is correct")
        print("3. Make sure your API key has the right permissions")
        print("4. Check if your API key has expired")
