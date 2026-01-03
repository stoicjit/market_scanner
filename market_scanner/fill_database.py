"""
Fill historical data for all symbols - daily, weekly, monthly timeframes
"""

from data_fetcher import DataFetcher
from db_manager import DBManager
import logging
import os
import time

# Setup logging
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler('logs/fill_historical.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def fill_all_historical():
    """Fill historical data for all 8 symbols across daily, weekly, monthly"""
    
    # Symbols to process
    symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'XRP/USDT', 
               'DOGE/USDT', 'LINK/USDT', 'ADA/USDT']
    
    # Timeframes to backfill
    timeframes = ['1d', '1w', '1M']
    
    # Timeframe name mapping for levels table
    timeframe_map = {
        '1d': 'daily',
        '1w': 'weekly', 
        '1M': 'monthly'
    }
    
    fetcher = DataFetcher()
    db = DBManager()
    
    total_symbols = len(symbols)
    total_operations = total_symbols * len(timeframes)
    completed = 0
    
    print("\n" + "="*70)
    print(f"Historical Data Backfill")
    print(f"Symbols: {total_symbols} | Timeframes: {len(timeframes)} | Total: {total_operations}")
    print("="*70)
    
    for symbol in symbols:
        db_symbol = fetcher.get_symbol_for_db(symbol)
        
        print(f"\n{'='*70}")
        print(f"Processing: {symbol} ({db_symbol})")
        print(f"{'='*70}")
        
        for timeframe in timeframes:
            try:
                completed += 1
                print(f"\n[{completed}/{total_operations}] {symbol} - {timeframe}")
                
                # Fetch data with indicators
                print(f"  → Fetching candles...")
                df = fetcher.fetch_with_indicators(symbol, timeframe, limit=1000)
                print(f"  ✓ Fetched {len(df)} complete candles")
                
                # Prepare candle records
                candle_records = fetcher.prepare_for_insert(df)
                
                # Extract levels
                high_records = [(row['high'], row['timestamp']) for _, row in df.iterrows()]
                low_records = [(row['low'], row['timestamp']) for _, row in df.iterrows()]
                
                # Insert candles
                print(f"  → Inserting candles into {db_symbol}_{timeframe}...")
                db.insert_ohlcv(db_symbol, timeframe, candle_records)
                
                # Insert high levels
                print(f"  → Inserting {len(high_records)} high levels...")
                db.insert_levels(db_symbol, timeframe_map[timeframe], high_records, 'high')
                
                # Insert low levels
                print(f"  → Inserting {len(low_records)} low levels...")
                db.insert_levels(db_symbol, timeframe_map[timeframe], low_records, 'low')
                
                print(f"  ✓ Completed {symbol} {timeframe}")
                
                # Small delay to respect rate limits
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing {symbol} {timeframe}: {e}")
                print(f"  ✗ FAILED: {e}")
                continue
    
    db.close()
    
    print("\n" + "="*70)
    print("✓ Historical data backfill complete!")
    print("="*70)
    
    # Summary
    print("\n--- Summary ---")
    for symbol in symbols:
        db_symbol = fetcher.get_symbol_for_db(symbol)
        print(f"\n{symbol} ({db_symbol}):")
        
        db_temp = DBManager()
        for timeframe in timeframes:
            try:
                count = db_temp.get_candle_count(db_symbol, timeframe)
                print(f"  {timeframe}: {count} candles")
            except:
                print(f"  {timeframe}: ERROR")
        db_temp.close()


if __name__ == '__main__':
    print("\n⚠️  WARNING: This will insert historical data for all symbols!")
    print("Symbols: BTC, ETH, LTC, XRP, DOGE, LINK, ADA")
    print("Timeframes: 1d, 1w, 1M")
    print("Total operations: 24 (7 symbols × 3 timeframes)")
    
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() == 'yes':
        fill_all_historical()
    else:
        print("Cancelled.")