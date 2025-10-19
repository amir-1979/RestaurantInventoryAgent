#!/usr/bin/env python3
"""
Test script to verify login credentials work correctly.
"""

import hashlib
import json
import os

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def test_credentials():
    """Test the default credentials"""
    DEFAULT_USERS = {

    }
    
    print("🔍 Testing Login System")
    print("=" * 40)
    
    # Create hashed users
    hashed_users = {username: hash_password(password) for username, password in DEFAULT_USERS.items()}
    
    # Test each credential
    for username, password in DEFAULT_USERS.items():
        input_hash = hash_password(password)
        stored_hash = hashed_users[username]
        
        if stored_hash == input_hash:
            print(f"✅ {username}/{password} - VALID")
        else:
            print(f"❌ {username}/{password} - INVALID")
            print(f"   Input hash:  {input_hash}")
            print(f"   Stored hash: {stored_hash}")
    
    # Check if users.json exists and test it
    if os.path.exists("users.json"):
        print("\n📁 Testing users.json file:")
        try:
            with open("users.json", 'r') as f:
                file_users = json.load(f)
            
            for username, password in DEFAULT_USERS.items():
                if username in file_users:
                    input_hash = hash_password(password)
                    stored_hash = file_users[username]
                    
                    if stored_hash == input_hash:
                        print(f"✅ {username} in file - VALID")
                    else:
                        print(f"❌ {username} in file - INVALID")
                else:
                    print(f"⚠️ {username} not found in file")
        except Exception as e:
            print(f"❌ Error reading users.json: {e}")
    else:
        print("\n📁 users.json file does not exist")
        
        # Create it
        try:
            with open("users.json", 'w') as f:
                json.dump(hashed_users, f, indent=2)
            print("✅ Created users.json file")
        except Exception as e:
            print(f"❌ Could not create users.json: {e}")
    
    print("\n" + "=" * 40)
    print("🔑 Use these credentials to login:")
    for username, password in DEFAULT_USERS.items():
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print()

if __name__ == "__main__":
    test_credentials()