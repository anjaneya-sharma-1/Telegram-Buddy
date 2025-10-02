#!/usr/bin/env python3
"""
Buddy Bot Launcher
Simplified script to start and manage the Buddy bot
"""

import os
import sys
import subprocess
from pathlib import Path


def run_bot():
    """Run the Buddy bot"""
        
    print("\n🚀 Starting Buddy bot...")
    print("Press Ctrl+C to stop the bot")
    print("-" * 40)
    
    try:
        # Get the Python executable path
        python_exe = Path("C:/Users/ANJANEYA/Desktop/Projects/telegram buddy/.venv/Scripts/python.exe")
        if not python_exe.exists():
            python_exe = "python"  # Fallback to system Python
            
        # Run the bot
        subprocess.run([str(python_exe), "buddy_bot.py"], cwd=Path(__file__).parent)
        
    except KeyboardInterrupt:
        print("\n\n👋 Buddy bot stopped. See you later!")
    except Exception as e:
        print(f"\n❌ Error running bot: {e}")

def main():
    """Main launcher function"""
    print("🤖 Buddy Bot Launcher")
    print("=" * 30)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        python_exe = Path("C:/Users/ANJANEYA/Desktop/Projects/telegram buddy/.venv/Scripts/python.exe")
        if not python_exe.exists():
            python_exe = "python"
        subprocess.run([str(python_exe), "test_buddy.py"])
    else:
        # Run the bot
        run_bot()

if __name__ == '__main__':
    main()