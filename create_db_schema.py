#!/usr/bin/env python3
"""
Database Schema Creation Script
Creates all necessary tables for the crypto fakeout scanner
"""

import psycopg2
import os
from psycopg2 import sql

# Database connection
DB_URL = os.getenv('DB_URL')

# Configuration
SYMBOLS = ['btcusdt', 'ethusdt', 'ltcusdt', 'xrpusdt', 'dogeusdt', 'xmrusdt', 'linkusdt', 'adausdt']
TIMEFRAMES = ['5m', '1h', '4h', '1d', '1w', '1M']


def create_ohlcv_table(cursor, symbol, timeframe):
    """Create OHLCV table for a specific symbol and timeframe"""
    
    table_name = f"{symbol}_{timeframe}"
    
    # Determine which columns to add based on timeframe
    has_fakeout_columns = timeframe in ['1h', '4h', '1d']
    
    # Build fakeout columns
    fakeout_columns = sql.SQL("")
    if has_fakeout_columns:
        fakeout_columns = sql.SQL("""
            is_fakeout BOOLEAN DEFAULT FALSE,
            fakeout_type TEXT,
            fakeout_level DOUBLE PRECISION,
        """)
    
    query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ UNIQUE NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            rsi_8 DOUBLE PRECISION,
            ema_20 DOUBLE PRECISION,
            ema_50 DOUBLE PRECISION,
            {fakeout_columns}
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS {timestamp_idx} ON {table} (timestamp DESC);
    """).format(
        table=sql.Identifier(table_name),
        fakeout_columns=fakeout_columns,
        timestamp_idx=sql.Identifier(f"{table_name}_timestamp_idx")
    )
    
    cursor.execute(query)
    
    # Create fakeout index separately if needed
    if has_fakeout_columns:
        cursor.execute(sql.SQL("""
            CREATE INDEX IF NOT EXISTS {fakeout_idx} ON {table} (is_fakeout) WHERE is_fakeout = TRUE;
        """).format(
            fakeout_idx=sql.Identifier(f"{table_name}_fakeout_idx"),
            table=sql.Identifier(table_name)
        ))
    
    print(f"✅ Created table: {table_name}")


def create_filtered_levels_tables(cursor):
    """Create tables for filtered levels (highs and lows)"""
    
    for level_type in ['high', 'low']:
        table_name = f"{level_type}_levels"
        
        cursor.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                level DOUBLE PRECISION NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """).format(table=sql.Identifier(table_name)))
        
        # Create indexes separately
        cursor.execute(sql.SQL("""
            CREATE INDEX IF NOT EXISTS {idx1} ON {table} (symbol, timeframe);
        """).format(
            idx1=sql.Identifier(f"{table_name}_symbol_timeframe_idx"),
            table=sql.Identifier(table_name)
        ))
        
        cursor.execute(sql.SQL("""
            CREATE INDEX IF NOT EXISTS {idx2} ON {table} (timestamp DESC);
        """).format(
            idx2=sql.Identifier(f"{table_name}_timestamp_idx"),
            table=sql.Identifier(table_name)
        ))
        
        print(f"✅ Created table: {table_name}")


def create_all_tables():
    """Create all necessary tables"""
    
    print("=" * 70)
    print("🗄️  DATABASE SCHEMA CREATION")
    print("=" * 70)
    
    if not DB_URL:
        print("❌ Error: DB_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Create OHLCV tables
        print(f"\n📊 Creating OHLCV tables...")
        print(f"Symbols: {len(SYMBOLS)}, Timeframes: {len(TIMEFRAMES)}")
        print(f"Total tables to create: {len(SYMBOLS) * len(TIMEFRAMES)}\n")
        
        for symbol in SYMBOLS:
            print(f"\n🔸 {symbol.upper()}")
            for timeframe in TIMEFRAMES:
                create_ohlcv_table(cursor, symbol, timeframe)
        
        # Create filtered levels tables
        print(f"\n📈 Creating filtered levels tables...\n")
        create_filtered_levels_tables(cursor)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✨ Database schema created successfully!")
        print("=" * 70)
        
        print(f"\n📊 Summary:")
        print(f"  • OHLCV tables: {len(SYMBOLS) * len(TIMEFRAMES)}")
        print(f"  • Filtered levels tables: 2 (high_levels, low_levels)")
        print(f"  • Total tables: {len(SYMBOLS) * len(TIMEFRAMES) + 2}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating schema: {e}")
        return False


def verify_tables():
    """Verify all tables were created"""
    
    print("\n" + "=" * 70)
    print("🔍 VERIFYING TABLES")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n✅ Found {len(tables)} tables:\n")
        
        # Group by symbol
        for symbol in SYMBOLS:
            symbol_tables = [t[0] for t in tables if t[0].startswith(symbol)]
            if symbol_tables:
                print(f"  {symbol.upper()}: {', '.join([t.split('_')[1] for t in symbol_tables])}")
        
        # Show filtered levels tables
        print(f"\n  Filtered levels:")
        level_tables = [t[0] for t in tables if 'levels' in t[0]]
        for table in level_tables:
            print(f"    • {table}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error verifying tables: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting database schema creation...\n")
    
    if create_all_tables():
        verify_tables()
        print("\n✨ Done! Your database is ready!")
    else:
        print("\n❌ Schema creation failed. Check the errors above.")