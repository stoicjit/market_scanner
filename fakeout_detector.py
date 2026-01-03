"""
Fakeout detection system
Checks candles against levels and marks fakeouts
"""

import psycopg2
import os
import logging
from dotenv import load_dotenv
from typing import List, Tuple, Optional

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler('logs/fakeout_detector.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class FakeoutDetector:
    """Detects fakeouts by comparing candles against key levels"""
    
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
    
    def get_levels(self, symbol: str, timeframe: str, level_type: str) -> List[float]:
        """
        Get all levels for a symbol/timeframe
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: 'daily', 'weekly', 'monthly'
            level_type: 'high' or 'low'
        
        Returns:
            List of level values
        """
        table_name = f'"{level_type}_levels"'
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT level FROM {table_name}
            WHERE symbol = %s AND timeframe = %s
            ORDER BY level
        """, (symbol, timeframe))
        
        results = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return results
    
    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[dict]:
        """
        Get the most recent candle from a table
        
        Returns:
            dict with candle data or None
        """
        table_name = f'"{symbol}_{timeframe}"'
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT timestamp, open, high, low, close, is_fakeout
            FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return {
                'timestamp': row[0],
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'is_fakeout': row[5]
            }
        return None
    
    def check_fakeout(self, candle: dict, levels: List[float], level_type: str) -> Optional[Tuple[str, float]]:
        """
        Check if a candle faked out any levels
        
        Args:
            candle: dict with OHLC data
            levels: list of level values to check
            level_type: 'high' or 'low'
        
        Returns:
            (fakeout_type, fakeout_level) or None if no fakeout
        
        Fakeout logic:
        - High fakeout: wick above level, close below
        - Low fakeout: wick below level, close above
        """
        high = candle['high']
        low = candle['low']
        close = candle['close']
        
        if level_type == 'high':
            # Check for high fakeouts
            for level in levels:
                if high > level and close < level:
                    logger.info(f"High fakeout detected at {level:.2f}")
                    return ('high', level)
        
        elif level_type == 'low':
            # Check for low fakeouts
            for level in levels:
                if low < level and close > level:
                    logger.info(f"Low fakeout detected at {level:.2f}")
                    return ('low', level)
        
        return None
    
    def mark_fakeout(self, symbol: str, timeframe: str, timestamp, fakeout_type: str, fakeout_level: float):
        """
        Mark a candle as a fakeout in the database
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: e.g., '1h', '4h', '1d'
            timestamp: candle timestamp
            fakeout_type: 'high' or 'low'
            fakeout_level: the level that was faked out
        """
        table_name = f'"{symbol}_{timeframe}"'
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE {table_name}
                SET is_fakeout = TRUE,
                    fakeout_type = %s,
                    fakeout_level = %s
                WHERE timestamp = %s
            """, (fakeout_type, fakeout_level, timestamp))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Marked {symbol} {timeframe} candle at {timestamp} as {fakeout_type} fakeout")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error marking fakeout: {e}")
            raise
    
    def check_hourly_fakeouts(self, symbol: str) -> bool:
        """
        Check latest 1h candle against daily levels
        
        Returns:
            True if fakeout detected, False otherwise
        """
        logger.info(f"Checking 1h fakeouts for {symbol}")
        
        # Get latest 1h candle
        candle = self.get_latest_candle(symbol, '1h')
        if not candle:
            logger.warning(f"No 1h candle found for {symbol}")
            return False
        
        # Skip if already marked as fakeout
        if candle['is_fakeout']:
            logger.info(f"Candle already marked as fakeout, skipping")
            return False
        
        # Get daily levels
        high_levels = self.get_levels(symbol, 'daily', 'high')
        low_levels = self.get_levels(symbol, 'daily', 'low')
        
        logger.info(f"Checking against {len(high_levels)} high levels and {len(low_levels)} low levels")
        
        # Check for high fakeout
        result = self.check_fakeout(candle, high_levels, 'high')
        if result:
            fakeout_type, level = result
            self.mark_fakeout(symbol, '1h', candle['timestamp'], fakeout_type, level)
            return True
        
        # Check for low fakeout
        result = self.check_fakeout(candle, low_levels, 'low')
        if result:
            fakeout_type, level = result
            self.mark_fakeout(symbol, '1h', candle['timestamp'], fakeout_type, level)
            return True
        
        logger.info("No fakeout detected")
        return False
    
    def check_4h_fakeouts(self, symbol: str) -> bool:
        """
        Check latest 4h candle against weekly levels
        
        Returns:
            True if fakeout detected, False otherwise
        """
        logger.info(f"Checking 4h fakeouts for {symbol}")
        
        candle = self.get_latest_candle(symbol, '4h')
        if not candle:
            logger.warning(f"No 4h candle found for {symbol}")
            return False
        
        if candle['is_fakeout']:
            logger.info(f"Candle already marked as fakeout, skipping")
            return False
        
        high_levels = self.get_levels(symbol, 'weekly', 'high')
        low_levels = self.get_levels(symbol, 'weekly', 'low')
        
        logger.info(f"Checking against {len(high_levels)} high levels and {len(low_levels)} low levels")
        
        # Check for high fakeout
        result = self.check_fakeout(candle, high_levels, 'high')
        if result:
            fakeout_type, level = result
            self.mark_fakeout(symbol, '4h', candle['timestamp'], fakeout_type, level)
            return True
        
        # Check for low fakeout
        result = self.check_fakeout(candle, low_levels, 'low')
        if result:
            fakeout_type, level = result
            self.mark_fakeout(symbol, '4h', candle['timestamp'], fakeout_type, level)
            return True
        
        logger.info("No fakeout detected")
        return False
    
    def check_daily_fakeouts(self, symbol: str) -> bool:
        """
        Check latest 1d candle against monthly levels
        
        Returns:
            True if fakeout detected, False otherwise
        """
        logger.info(f"Checking daily fakeouts for {symbol}")
        
        candle = self.get_latest_candle(symbol, '1d')
        if not candle:
            logger.warning(f"No daily candle found for {symbol}")
            return False
        
        if candle['is_fakeout']:
            logger.info(f"Candle already marked as fakeout, skipping")
            return False
        
        high_levels = self.get_levels(symbol, 'monthly', 'high')
        low_levels = self.get_levels(symbol, 'monthly', 'low')
        
        logger.info(f"Checking against {len(high_levels)} high levels and {len(low_levels)} low levels")
        
        # Check for high fakeout
        result = self.check_fakeout(candle, high_levels, 'high')
        if result:
            fakeout_type, level = result
            self.mark_fakeout(symbol, '1d', candle['timestamp'], fakeout_type, level)
            return True
        
        # Check for low fakeout
        result = self.check_fakeout(candle, low_levels, 'low')
        if result:
            fakeout_type, level = result
            self.mark_fakeout(symbol, '1d', candle['timestamp'], fakeout_type, level)
            return True
        
        logger.info("No fakeout detected")
        return False
    
    def check_all_symbols(self, timeframe: str):
        """
        Check all symbols for a specific timeframe
        
        Args:
            timeframe: '1h', '4h', or '1d'
        """
        symbols = ['btcusdt', 'ethusdt', 'ltcusdt', 'xrpusdt', 
                   'dogeusdt', 'linkusdt', 'adausdt']
        
        method_map = {
            '1h': self.check_hourly_fakeouts,
            '4h': self.check_4h_fakeouts,
            '1d': self.check_daily_fakeouts
        }
        
        if timeframe not in method_map:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        check_method = method_map[timeframe]
        fakeouts_found = 0
        
        for symbol in symbols:
            if check_method(symbol):
                fakeouts_found += 1
        
        logger.info(f"Total fakeouts found for {timeframe}: {fakeouts_found}")


def test_detector():
    """Test the fakeout detector"""
    detector = FakeoutDetector()
    
    print("\n" + "="*70)
    print("Testing Fakeout Detector")
    print("="*70)
    
    # Test 1h fakeouts
    print("\n--- Checking 1h fakeouts (vs daily levels) ---")
    detector.check_all_symbols('1h')
    
    detector.close()
    
    print("\n" + "="*70)
    print("✓ Test complete")
    print("="*70)


if __name__ == '__main__':
    test_detector()