#!/usr/bin/env python3
"""
Database Test Runner
Convenience script to run database tests with proper uv environment
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run database tests using uv"""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Change to the database directory
    os.chdir(script_dir)
    
    print("🔧 Running PII Encryption Database Tests with uv...")
    print(f"📁 Working directory: {script_dir}")
    print("=" * 60)
    
    try:
        # Run the test script using uv
        result = subprocess.run([
            "uv", "run", "python", "test_connection.py"
        ], check=True)
        
        print("\n✅ Database tests completed successfully!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Database tests failed with exit code: {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("\n❌ Error: 'uv' command not found.")
        print("Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())