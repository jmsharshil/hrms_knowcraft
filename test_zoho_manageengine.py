#!/usr/bin/env python
"""
Test script for Zoho ManageEngine API initiation.
Run with: python test_zoho_manageengine.py
"""

import os
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_knowcraft.settings')
django.setup()

from onboarding.utils.zoho_manageengine import ManageEngineClient
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_initiation():
    print("🔧 Testing Zoho ManageEngine Client Initiation...")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['ZOHO_CLIENT_ID', 'ZOHO_CLIENT_SECRET', 'ZOHO_REFRESH_TOKEN']
    print("📋 Checking environment variables:")
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: [SET]")
        else:
            print(f"  ❌ {var}: [MISSING]")
            missing.append(var)
    
    if missing:
        print("\n⚠️  Missing credentials! Please add these to your .env file:")
        for var in missing:
            print(f"   {var}=your_value_here")
        print("\nYou can get these from Zoho ManageEngine developer console.")
        return False
    
    # Initialize client
    print("\n🚀 Initializing ManageEngineClient...")
    try:
        client = ManageEngineClient()
        print("✅ Client initialized successfully!")
        
        # Test token retrieval
        print("\n🔑 Testing access token retrieval...")
        token = client._get_access_token()
        if token:
            print("✅ Access token retrieved successfully!")
            print(f"   Token preview: {token[:20]}...{token[-10:]}")
            
            # Test headers
            headers = client._get_headers()
            if headers:
                print("✅ Headers generated successfully!")
                print(f"   Authorization: {headers.get('Authorization', 'N/A')[:30]}...")
                return True
            else:
                print("❌ Failed to generate headers")
                return False
        else:
            print("❌ Failed to get access token")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_initiation()
    if success:
        print("\n🎉 Zoho ManageEngine API initiation test PASSED!")
    else:
        print("\n❌ Test failed. Check the errors above.")
