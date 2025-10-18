#!/usr/bin/env python3
"""
Simple launcher script for the Streamlit inventory dashboard.
This script will start the Streamlit server and open the dashboard in your browser.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit inventory dashboard."""
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("❌ Streamlit is not installed.")
        print("📦 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
    
    # Check if inventory.csv exists
    if not os.path.exists("inventory.csv"):
        print("❌ inventory.csv not found in current directory.")
        print("Please make sure inventory.csv is in the same directory as this script.")
        return
    
    print("🚀 Starting Inventory Dashboard...")
    print("📊 The dashboard will open in your browser automatically.")
    print("🔗 If it doesn't open, go to: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Launch Streamlit - use simple secure version by default
    dashboard_file = "simple_secure_dashboard.py"
    
    # Check if user wants other versions
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            dashboard_file = "streamlit_inventory_app.py"
            print("🤖 Using full dashboard with AI features...")
        elif sys.argv[1] == "--simple":
            dashboard_file = "simple_dashboard.py"
            print("📊 Using simple dashboard...")
        elif sys.argv[1] == "--bulletproof":
            dashboard_file = "bulletproof_dashboard.py"
            print("🛡️ Using bulletproof dashboard...")
        elif sys.argv[1] == "--ultra-safe":
            dashboard_file = "ultra_safe_dashboard.py"
            print("🔒 Using ultra-safe dashboard...")
        elif sys.argv[1] == "--secure":
            dashboard_file = "secure_dashboard.py"
            print("� UUsing advanced secure dashboard...")
        elif sys.argv[1] == "--no-auth":
            dashboard_file = "ultra_safe_dashboard.py"
            print("🔓 Using dashboard without authentication...")
        else:
            print("🔐 Using simple secure dashboard with login (default)...")
    else:
        print("🔐 Using simple secure dashboard with login (use --no-auth to skip login, --full for AI features)...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_file,
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped. Thanks for using the Inventory Dashboard!")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    main()