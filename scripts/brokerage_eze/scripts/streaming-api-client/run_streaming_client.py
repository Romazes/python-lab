#!/usr/bin/env python3
"""
Run script for the Streaming API Client
This script helps you get started with the streaming client application.
"""

import os
import sys
import shutil

def check_requirements():
    """Check if all required files are present."""
    # Get the parent directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)

    required_files = [
        'emsxapilibrary.py',
        'market_data_pb2.py',
        'market_data_pb2_grpc.py',
        'utilities_pb2.py',
        'utilities_pb2_grpc.py'
    ]

    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(parent_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(full_path)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all EMSX API Python files are in the parent 'scripts' directory.")
        return False

    print("✅ All required files found.")
    return True

def check_config():
    """Check if config.cfg exists in the parent directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    parent_config = os.path.join(parent_dir, 'config.cfg')

    if not os.path.exists(parent_config):
        print("❌ config.cfg not found in parent directory.")
        print("Please ensure config.cfg exists in the parent 'scripts' directory with your EMSX server credentials.")
        return False

    print("✅ Configuration file found in parent directory.")
    return True

def main():
    """Main setup and run function."""
    print("=== Streaming API Client Setup ===")

    # Add parent directory to Python path for imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Check requirements
    if not check_requirements():
        return 1

    # Check configuration
    if not check_config():
        return 1

    # Run the application
    print("\n🚀 Starting Streaming API Client...")
    print("Use Ctrl+C to exit the application.\n")

    # Import and run the main application
    try:
        from streaming_client_app import main as app_main
        import asyncio
        asyncio.run(app_main())
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())