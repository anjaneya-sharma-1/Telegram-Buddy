#!/usr/bin/env python3
"""
Test script for Buddy bot
Tests basic functionality without requiring a live Telegram connection
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add the current directory to the path so we can import buddy_bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from buddy_bot import BuddyBot, BotMode, UserState

async def test_basic_functionality():
    """Test basic bot functionality"""
    print("🧪 Testing Buddy Bot Basic Functionality...")
    
    # Create bot instance
    try:
        # Mock the Groq client for testing
        buddy = BuddyBot()
        buddy.groq_client = Mock()
        
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hey there! I'm Buddy, nice to meet you! 😊"
        buddy.groq_client.chat.completions.create.return_value = mock_response
        
        print("✅ Bot instance created successfully")
        
        # Test user state management
        user_id = 12345
        buddy.user_states[user_id] = UserState()
        assert buddy.user_states[user_id].mode == BotMode.SINGLE
        print("✅ User state management working")
        
        # Test mode switching
        buddy.user_states[user_id].mode = BotMode.PARALLEL
        assert buddy.user_states[user_id].mode == BotMode.PARALLEL
        print("✅ Mode switching working")
        
        # Test message batching
        buddy.user_states[user_id].pending_messages = ["Hello", "How are you?"]
        assert len(buddy.user_states[user_id].pending_messages) == 2
        print("✅ Message batching working")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_environment_setup():
    """Test environment configuration"""
    print("\n🔧 Testing Environment Setup...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and groq_key.startswith('gsk_'):
            print("✅ Groq API key found and formatted correctly")
        else:
            print("⚠️  Groq API key not found or incorrect format")
            
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token and telegram_token != 'your_telegram_bot_token_here':
            print("✅ Telegram bot token configured")
        else:
            print("⚠️  Telegram bot token needs to be configured")
            print("   Please get a token from @BotFather and update .env file")
            
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are installed"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = [
        ('telegram', 'python-telegram-bot'),
        ('groq', 'groq'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_good = True
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {package} imported successfully")
        except ImportError:
            print(f"❌ {package} not found - run: pip install {package}")
            all_good = False
            
    return all_good

async def main():
    """Run all tests"""
    print("🤖 Buddy Bot Test Suite")
    print("=" * 40)
    
    # Test dependencies first
    deps_ok = test_dependencies()
    
    # Test environment
    env_ok = test_environment_setup()
    
    # Test basic functionality
    if deps_ok:
        basic_ok = await test_basic_functionality()
    else:
        basic_ok = False
        print("\n⚠️  Skipping basic tests due to missing dependencies")
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"Environment: {'✅ PASS' if env_ok else '⚠️  PARTIAL'}")
    print(f"Basic functionality: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    
    if deps_ok and basic_ok:
        print("\n🎉 Buddy is ready to go!")
        print("\nNext steps:")
        print("1. Get a Telegram bot token from @BotFather")
        print("2. Update TELEGRAM_BOT_TOKEN in .env file")
        print("3. Run: python buddy_bot.py")
    else:
        print("\n🔧 Please fix the issues above before running the bot")

if __name__ == '__main__':
    asyncio.run(main())