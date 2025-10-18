#!/usr/bin/env python3
"""
User setup script for the secure inventory dashboard.
This script helps you create and manage user accounts.
"""

import json
import hashlib
import getpass
import os

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load existing users"""
    users_file = "users.json"
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to file"""
    try:
        with open("users.json", 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def add_user():
    """Add a new user"""
    users = load_users()
    
    print("\n=== Add New User ===")
    username = input("Enter username: ").strip()
    
    if not username:
        print("❌ Username cannot be empty")
        return
    
    if username in users:
        print(f"❌ User '{username}' already exists")
        return
    
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("❌ Passwords don't match")
        return
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters long")
        return
    
    users[username] = hash_password(password)
    
    if save_users(users):
        print(f"✅ User '{username}' added successfully!")
    else:
        print("❌ Failed to save user")

def list_users():
    """List all users"""
    users = load_users()
    
    if not users:
        print("\n📝 No users found")
        return
    
    print(f"\n👥 Current Users ({len(users)}):")
    for username in users.keys():
        print(f"   • {username}")

def delete_user():
    """Delete a user"""
    users = load_users()
    
    if not users:
        print("\n📝 No users to delete")
        return
    
    print("\n=== Delete User ===")
    list_users()
    
    username = input("\nEnter username to delete: ").strip()
    
    if username not in users:
        print(f"❌ User '{username}' not found")
        return
    
    confirm = input(f"Are you sure you want to delete '{username}'? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        del users[username]
        if save_users(users):
            print(f"✅ User '{username}' deleted successfully!")
        else:
            print("❌ Failed to delete user")
    else:
        print("❌ Deletion cancelled")

def reset_password():
    """Reset a user's password"""
    users = load_users()
    
    if not users:
        print("\n📝 No users found")
        return
    
    print("\n=== Reset Password ===")
    list_users()
    
    username = input("\nEnter username: ").strip()
    
    if username not in users:
        print(f"❌ User '{username}' not found")
        return
    
    new_password = getpass.getpass("Enter new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    
    if new_password != confirm_password:
        print("❌ Passwords don't match")
        return
    
    if len(new_password) < 6:
        print("❌ Password must be at least 6 characters long")
        return
    
    users[username] = hash_password(new_password)
    
    if save_users(users):
        print(f"✅ Password for '{username}' reset successfully!")
    else:
        print("❌ Failed to reset password")

def create_default_users():
    """Create default users for demo"""
    default_users = {
        "admin": "admin123",
        "manager": "manager123", 
        "staff": "staff123"
    }
    
    users = load_users()
    added_count = 0
    
    for username, password in default_users.items():
        if username not in users:
            users[username] = hash_password(password)
            added_count += 1
    
    if added_count > 0:
        if save_users(users):
            print(f"✅ Created {added_count} default users")
            print("\nDefault credentials:")
            for username, password in default_users.items():
                print(f"   • {username}: {password}")
        else:
            print("❌ Failed to create default users")
    else:
        print("ℹ️ Default users already exist")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("🔐 Inventory Dashboard - User Management")
        print("="*50)
        print("1. 👤 Add new user")
        print("2. 👥 List all users")
        print("3. 🗑️  Delete user")
        print("4. 🔑 Reset password")
        print("5. 🏗️  Create default users (demo)")
        print("6. 🚪 Exit")
        print("-"*50)
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == '1':
            add_user()
        elif choice == '2':
            list_users()
        elif choice == '3':
            delete_user()
        elif choice == '4':
            reset_password()
        elif choice == '5':
            create_default_users()
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please choose 1-6.")

if __name__ == "__main__":
    main()