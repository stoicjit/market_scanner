"""
Level filtering for high and low levels
Filters to keep only significant levels based on greedy algorithm
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
    """Filters high and low levels using greedy decreasing/increasing algorithm"""
    
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
    
    def get_levels(self, symbol: str, timeframe: str, level_type: str):
        """
        Get all levels for a symbol/timeframe, ordered by timestamp
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: 'daily', 'weekly', 'monthly'
            level_type: 'high' or 'low'
        
        Returns:
            List of tuples: (id, level, timestamp)
        """
        table_name = f'"{level_type}_levels"'
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT id, level, timestamp 
            FROM {table_name}
            WHERE symbol = %s AND timeframe = %s
            ORDER BY timestamp ASC
        """, (symbol, timeframe))
        
        results = cursor.fetchall()
        cursor.close()
        logger.info(f"Fetched {len(results)} {level_type} levels for {symbol} {timeframe}")
        return results
    
    def filter_highs(self, symbol: str, timeframe: str):
        """
        Filter high levels - most recent must be highest
        Keep only levels that form decreasing sequence from new to old
        
        Logic:
        - Keep most recent high (always)
        - Going backwards in time, only keep highs that are HIGHER than current max
        
        Example: [3,9,4,7,2,3,6,2,4] -> [9,7,6,4]
        
        Returns:
            (kept_count, deleted_count)
        """
        levels = self.get_levels(symbol, timeframe, 'high')
        
        if not levels:
            logger.info("No high levels to filter")
            return 0, 0
        
        logger.info(f"Filtering {len(levels)} high levels for {symbol} {timeframe}")
        
        keep_ids = []
        levels_reversed = list(reversed(levels))
        
        # Keep most recent
        most_recent_id, most_recent_level, most_recent_ts = levels_reversed[0]
        keep_ids.append(most_recent_id)
        max_kept = most_recent_level
        logger.debug(f"Keeping most recent high: {most_recent_level:.2f} at {most_recent_ts}")
        
        # Go through older candles
        for level_id, level, timestamp in levels_reversed[1:]:
            if level > max_kept:
                keep_ids.append(level_id)
                max_kept = level
                logger.debug(f"Keeping older high: {level:.2f} at {timestamp}")
            else:
                logger.debug(f"Deleting high: {level:.2f} at {timestamp} (not higher than {max_kept:.2f})")
        
        kept_count = len(keep_ids)
        deleted_count = len(levels) - kept_count
        
        # Delete levels not in keep list
        if deleted_count > 0:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM "high_levels"
                WHERE symbol = %s AND timeframe = %s AND id NOT IN %s
            """, (symbol, timeframe, tuple(keep_ids)))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Filtered highs for {symbol} {timeframe}: kept {kept_count}, deleted {deleted_count}")
        else:
            logger.info(f"No highs to delete for {symbol} {timeframe}")
        
        return kept_count, deleted_count
    
    def filter_lows(self, symbol: str, timeframe: str):
        """
        Filter low levels - most recent must be lowest
        Keep only levels that form increasing sequence from new to old
        
        Logic:
        - Keep most recent low (always)
        - Going backwards in time, only keep lows that are LOWER than current min
        
        Example: [9,3,6,4,8,7,5,8,6] -> [3,4,5,6]
        
        Returns:
            (kept_count, deleted_count)
        """
        levels = self.get_levels(symbol, timeframe, 'low')
        
        if not levels:
            logger.info("No low levels to filter")
            return 0, 0
        
        logger.info(f"Filtering {len(levels)} low levels for {symbol} {timeframe}")
        
        keep_ids = []
        levels_reversed = list(reversed(levels))
        
        # Keep most recent
        most_recent_id, most_recent_level, most_recent_ts = levels_reversed[0]
        keep_ids.append(most_recent_id)
        min_kept = most_recent_level
        logger.debug(f"Keeping most recent low: {most_recent_level:.2f} at {most_recent_ts}")
        
        # Go through older candles
        for level_id, level, timestamp in levels_reversed[1:]:
            if level < min_kept:
                keep_ids.append(level_id)
                min_kept = level
                logger.debug(f"Keeping older low: {level:.2f} at {timestamp}")
            else:
                logger.debug(f"Deleting low: {level:.2f} at {timestamp} (not lower than {min_kept:.2f})")
        
        kept_count = len(keep_ids)
        deleted_count = len(levels) - kept_count
        
        # Delete levels not in keep list
        if deleted_count > 0:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM "low_levels"
                WHERE symbol = %s AND timeframe = %s AND id NOT IN %s
            """, (symbol, timeframe, tuple(keep_ids)))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Filtered lows for {symbol} {timeframe}: kept {kept_count}, deleted {deleted_count}")
        else:
            logger.info(f"No lows to delete for {symbol} {timeframe}")
        
        return kept_count, deleted_count
    
    def filter_symbol_timeframe(self, symbol: str, timeframe: str):
        """
        Filter both high and low levels for a symbol/timeframe
        
        Returns:
            dict with results: {'highs': (kept, deleted), 'lows': (kept, deleted)}
        """
        logger.info(f"Filtering levels for {symbol} {timeframe}")
        
        highs = self.filter_highs(symbol, timeframe)
        lows = self.filter_lows(symbol, timeframe)
        
        return {
            'highs': highs,
            'lows': lows
        }
    
    def filter_all(self):
        """
        Filter levels for all symbols and timeframes
        Processes: 7 symbols × 3 timeframes = 21 combinations
        """
        symbols = ['btcusdt', 'ethusdt', 'ltcusdt', 'xrpusdt', 
                   'dogeusdt', 'linkusdt', 'adausdt']
        timeframes = ['daily', 'weekly', 'monthly']
        
        results = {}
        
        for symbol in symbols:
            results[symbol] = {}
            for timeframe in timeframes:
                print(f"\nFiltering {symbol} {timeframe}...")
                result = self.filter_symbol_timeframe(symbol, timeframe)
                results[symbol][timeframe] = result
                
                print(f"  Highs: kept {result['highs'][0]}, deleted {result['highs'][1]}")
                print(f"  Lows: kept {result['lows'][0]}, deleted {result['lows'][1]}")
        
        return results


def filter_all_levels():
    """Filter all levels after initial backfill"""
    
    print("\n" + "="*70)
    print("Filtering All Levels")
    print("="*70)
    
    filter_obj = LevelFilter()
    results = filter_obj.filter_all()
    filter_obj.close()
    
    # Summary
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    
    total_highs_kept = 0
    total_highs_deleted = 0
    total_lows_kept = 0
    total_lows_deleted = 0
    
    for symbol, timeframes in results.items():
        print(f"\n{symbol.upper()}:")
        for tf, result in timeframes.items():
            hk, hd = result['highs']
            lk, ld = result['lows']
            print(f"  {tf}: H({hk} kept, {hd} del) | L({lk} kept, {ld} del)")
            
            total_highs_kept += hk
            total_highs_deleted += hd
            total_lows_kept += lk
            total_lows_deleted += ld
    
    print(f"\n{'='*70}")
    print(f"Total High Levels: {total_highs_kept} kept, {total_highs_deleted} deleted")
    print(f"Total Low Levels: {total_lows_kept} kept, {total_lows_deleted} deleted")
    print(f"{'='*70}")


if __name__ == '__main__':
    filter_all_levels()