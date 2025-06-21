"""
Test script for Basic Tech API integration.
This script tests the ability to store and retrieve user context data.
"""

import os
import json
import time
from dotenv import load_dotenv
from utils.basic_tech_api import BasicTechAPI

# Load environment variables
load_dotenv()

# Get user ID from environment or use default
user_id = os.environ.get('FIXER_USER_ID', 'did:tmp:6673b487aa82727924a89f44')

def test_basic_tech_integration():
    """Test Basic Tech API integration by storing and retrieving user context."""
    print("🧪 Testing Basic Tech API Integration")
    print("=" * 40)
    
    # Initialize Basic Tech client
    basic_tech = BasicTechAPI()
    
    # Check if credentials are available
    if not basic_tech.api_key or not basic_tech.project_id:
        print("❌ Basic Tech API key or Project ID not set.")
        return False
    
    print(f"📋 Project ID: {basic_tech.project_id}")
    print(f"👤 User ID: {user_id}")
    print(f"📊 Table: {basic_tech.table_id}")
    
    # Test 1: Get current user context (may be empty)
    print("\n🔍 Test 1: Getting current user context...")
    current_context = basic_tech.get_user_context(user_id)
    if current_context is not None:
        print("✅ Successfully retrieved user context")
        print(f"📝 Current context: {json.dumps(current_context, indent=2)}")
    else:
        print("⚠️ No existing context found or table doesn't exist")
    
    # Test 2: Update user context with test data
    print("\n🔄 Test 2: Updating user context with test data...")
    test_context = {
        "interactions": [],
        "preferences": {
            "theme": "dark",
            "language": "en",
            "notifications": True
        },
        "device_info": {
            "os": "Windows",
            "browser": "Chrome",
            "device": "Desktop"
        },
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    success = basic_tech.update_user_context(user_id, test_context)
    if success:
        print("✅ Successfully updated user context")
    else:
        print("❌ Failed to update user context")
        return False
    
    # Test 3: Add an interaction
    print("\n➕ Test 3: Adding an interaction...")
    interaction = {
        "timestamp": time.time(),
        "request": "Test request from integration test",
        "response": "Test response from integration test",
        "metadata": {
            "test_id": "integration_test_1"
        }
    }
    
    success = basic_tech.add_interaction_to_context(user_id, interaction)
    if success:
        print("✅ Successfully added interaction to user context")
    else:
        print("❌ Failed to add interaction to user context")
        return False
    
    # Test 4: Verify updated context
    print("\n🔍 Test 4: Verifying updated context...")
    updated_context = basic_tech.get_user_context(user_id)
    if updated_context and "interactions" in updated_context and len(updated_context["interactions"]) > 0:
        print("✅ Successfully verified user context with interaction")
        print(f"📝 Updated context: {json.dumps(updated_context, indent=2)}")
    else:
        print("❌ Failed to verify updated context")
        return False
    
    print("\n🎉 All tests passed! Basic Tech integration is working correctly.")
    return True

if __name__ == "__main__":
    test_basic_tech_integration()
