"""
Test level filtering for high levels
Implements greedy decreasing algorithm
"""

import psycopg2
import os
import logging

# Setup logging
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler('logs/level_filter.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class LevelFilter:
    """Filters high and low levels using greedy algorithm"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DB_URL')
        if not self.db_url:
            raise ValueError("DB_URL not provided")
        
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = False
        logger.info("Connected to database")
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_high_levels(self, symbol: str, timeframe: str):
        """
        Get all high levels for a symbol/timeframe, ordered by timestamp
        
        Returns:
            List of tuples: (id, level, timestamp)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, level, timestamp 
            FROM high_levels 
            WHERE symbol = %s AND timeframe = %s
            ORDER BY timestamp ASC
        """, (symbol, timeframe))
        
        results = cursor.fetchall()
        cursor.close()
        logger.info(f"Fetched {len(results)} high levels for {symbol} {timeframe}")
        return results
    
    def filter_highs(self, symbol: str, timeframe: str):
        """
        Filter high levels - keep only decreasing sequence from most recent
        Greedy decreasing: work backwards, keep levels that decrease
        
        Example: [3,9,4,7,2,3,6,2,4] -> [9,7,6,4]
        
        Returns:
            (kept_count, deleted_count)
        """
        levels = self.get_high_levels(symbol, timeframe)
        
        if not levels:
            logger.info("No levels to filter")
            return 0, 0
        
        logger.info(f"Starting filter with {len(levels)} levels")
        
        # Track which IDs to keep
        keep_ids = []
        
        # Work backwards from most recent
        min_so_far = float('inf')
        
        for level_id, level, timestamp in reversed(levels):
            if level < min_so_far:
                keep_ids.append(level_id)
                min_so_far = level
                logger.debug(f"Keeping level {level:.2f} at {timestamp}")
            else:
                logger.debug(f"Removing level {level:.2f} at {timestamp} (not lower than {min_so_far:.2f})")
        
        kept_count = len(keep_ids)
        deleted_count = len(levels) - kept_count
        
        # Delete levels not in keep list
        if deleted_count > 0:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                DELETE FROM high_levels 
                WHERE symbol = %s AND timeframe = %s AND id NOT IN %s
            """, (symbol, timeframe, tuple(keep_ids)))
            
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Filtered highs: kept {kept_count}, deleted {deleted_count}")
        else:
            logger.info("No levels to delete - all form decreasing sequence")
        
        return kept_count, deleted_count
    
    def get_filtered_levels_preview(self, symbol: str, timeframe: str, limit: int = 10):
        """Show first and last N filtered levels"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT level, timestamp 
            FROM high_levels 
            WHERE symbol = %s AND timeframe = %s
            ORDER BY timestamp ASC
        """, (symbol, timeframe))
        
        results = cursor.fetchall()
        cursor.close()
        
        print(f"\n--- First {limit} Filtered High Levels ---")
        for level, timestamp in results[:limit]:
            print(f"  {timestamp} | ${level:.2f}")
        
        if len(results) > limit * 2:
            print(f"\n  ... ({len(results) - limit * 2} more) ...\n")
        
        print(f"--- Last {limit} Filtered High Levels ---")
        for level, timestamp in results[-limit:]:
            print(f"  {timestamp} | ${level:.2f}")
        
        return len(results)


def test_filter_btc_weekly_highs():
    """Test filtering BTC weekly high levels"""
    
    print("\n" + "="*60)
    print("Testing High Level Filtering - BTC Weekly")
    print("="*60)
    
    filter = LevelFilter()
    
    # Show count before filtering
    cursor = filter.conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM high_levels 
        WHERE symbol = 'btcusdt' AND timeframe = 'weekly'
    """)
    before_count = cursor.fetchone()[0]
    cursor.close()
    
    print(f"\nBefore filtering: {before_count} high levels")
    
    # Filter
    print("\nApplying greedy filter (keep only higher highs)...")
    kept, deleted = filter.filter_highs('btcusdt', 'weekly')
    
    print(f"\nAfter filtering:")
    print(f"  ✓ Kept: {kept} levels")
    print(f"  ✗ Deleted: {deleted} levels")
    print(f"  Reduction: {deleted/before_count*100:.1f}%")
    
    # Show preview of filtered levels
    total = filter.get_filtered_levels_preview('btcusdt', 'weekly', limit=5)
    
    filter.close()
    
    print("\n" + "="*60)
    print("✓ Filtering test complete!")
    print("="*60)


if __name__ == '__main__':
    test_filter_btc_weekly_highs()