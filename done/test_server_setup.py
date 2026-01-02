#!/usr/bin/env python3
"""
Simple test script to verify server setup
Tests: Python version, dependencies, PostgreSQL connection, file system
"""

import sys
import os
from datetime import datetime

def test_python_version():
    """Check Python version"""
    print("🐍 Testing Python Version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Python version is good!\n")
        return True
    else:
        print("   ❌ Need Python 3.8 or higher\n")
        return False


def test_dependencies():
    """Check if required packages are installed"""
    print("📦 Testing Dependencies...")
    
    required = {
        'ccxt': 'CCXT (Binance API)',
        'pandas': 'Pandas',
        'pandas_ta': 'Pandas-TA (indicators)',
        'psycopg2': 'PostgreSQL driver',
        'telegram': 'Telegram bot'
    }
    
    results = {}
    for module, description in required.items():
        try:
            __import__(module)
            print(f"   ✅ {description}")
            results[module] = True
        except ImportError:
            print(f"   ❌ {description} - NOT INSTALLED")
            results[module] = False
    
    print()
    return all(results.values())


def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("🐘 Testing PostgreSQL Connection...")
    
    db_url = os.getenv('DB_URL')
    
    if not db_url:
        print("   ⚠️  DB_URL environment variable not set")
        print("   Run: export DB_URL='your_postgres_url'\n")
        return False
    
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   ✅ Connected to PostgreSQL")
        print(f"   Version: {version[0][:50]}...\n")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}\n")
        return False


def test_telegram_config():
    """Test Telegram configuration"""
    print("📱 Testing Telegram Config...")
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token:
        print("   ⚠️  BOT_TOKEN not set")
        token_ok = False
    else:
        print("   ✅ BOT_TOKEN is set")
        token_ok = True
    
    if not chat_id:
        print("   ⚠️  CHAT_ID not set")
        chat_ok = False
    else:
        print("   ✅ CHAT_ID is set")
        chat_ok = True
    
    print()
    return token_ok and chat_ok


def test_binance_connection():
    """Test Binance API connection"""
    print("🟡 Testing Binance Connection...")
    
    try:
        import ccxt
        binance = ccxt.binance()
        ticker = binance.fetch_ticker('BTC/USDT')
        price = ticker['last']
        print(f"   ✅ Connected to Binance")
        print(f"   BTC/USDT price: ${price:,.2f}\n")
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}\n")
        return False


def test_file_write():
    """Test file write permissions"""
    print("📝 Testing File Write Permissions...")
    
    test_file = 'test_write.txt'
    
    try:
        with open(test_file, 'w') as f:
            f.write(f"Test write at {datetime.now()}")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        os.remove(test_file)
        print("   ✅ Can write and read files\n")
        return True
    except Exception as e:
        print(f"   ❌ File operations failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 SERVER SETUP TEST")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Running on: {os.uname().nodename if hasattr(os, 'uname') else 'Unknown'}\n")
    
    tests = {
        'Python Version': test_python_version(),
        'Dependencies': test_dependencies(),
        'PostgreSQL': test_postgres_connection(),
        'Telegram Config': test_telegram_config(),
        'Binance API': test_binance_connection(),
        'File System': test_file_write()
    }
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(tests.values())
    total = len(tests)
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✨ All tests passed! Server is ready! 🚀")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix issues before deploying.")
        return 1


if __name__ == "__main__":
    exit(main())