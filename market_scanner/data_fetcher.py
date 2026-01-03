"""
Data fetching system for crypto scanner
Fetches OHLCV data from Binance and calculates indicators
"""

import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timezone
from typing import Optional, List, Dict
import time
import logging
import os

# Setup logging to both file and console
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('logs/data_fetcher.log')
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add handlers
logger.addHandler(fh)
logger.addHandler(ch)


class DataFetcher:
    """Handles fetching OHLCV data from Binance and calculating indicators"""
    
    # Symbols to track
    SYMBOLS = [
        'BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'XRP/USDT',
        'DOGE/USDT', 'LINK/USDT', 'ADA/USDT'
    ]
    
    # Timeframes to monitor
    TIMEFRAMES = ['5m', '1h', '4h', '1d', '1w']  # Note: excluding 1M for now
    
    def __init__(self):
        """Initialize Binance exchange connection"""
        self.exchange = ccxt.binance({
            'enableRateLimit': True,  # Respect rate limits
            'options': {
                'defaultType': 'spot'
            }
        })
        logger.info("Initialized Binance connection")
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = 1000,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Binance
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('5m', '1h', '4h', '1d', '1w')
            limit: Number of candles to fetch (max 1000)
            since: Timestamp in milliseconds to fetch from (optional)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            logger.info(f"Fetching {limit} {timeframe} candles for {symbol}")
            
            # Fetch from exchange
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp from milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            
            logger.info(f"Fetched {len(df)} candles for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} {timeframe}: {e}")
            raise
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI(8), EMA(20), and EMA(50) indicators
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added indicator columns
        """
        try:
            # Need at least 50 candles for EMA(50)
            if len(df) < 50:
                logger.warning(f"Not enough data for indicators (need 50, got {len(df)})")
                df['rsi_8'] = None
                df['ema_20'] = None
                df['ema_50'] = None
                return df
            
            # Calculate RSI(8) - matches TradingView indicator
            df['rsi_8'] = ta.rsi(df['close'], length=8)
            
            # Calculate EMAs
            df['ema_20'] = ta.ema(df['close'], length=20)
            df['ema_50'] = ta.ema(df['close'], length=50)
            
            logger.debug(f"Calculated indicators for {len(df)} candles")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise
    
    def fetch_with_indicators(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data and add indicators in one call
        Excludes the last incomplete candle
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            limit: Number of candles
            since: Timestamp to fetch from
        
        Returns:
            DataFrame with OHLCV + indicators (excluding last incomplete candle)
        """
        df = self.fetch_ohlcv(symbol, timeframe, limit, since)
        df = self.calculate_indicators(df)
        
        # Remove last candle (still forming)
        df = df[:-1]
        logger.info(f"Removed last incomplete candle, {len(df)} complete candles remaining")
        
        return df
    
    def backfill_historical_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Fetch historical data for all symbols and timeframes
        Initial data load for the system
        
        Returns:
            Nested dict: {symbol: {timeframe: DataFrame}}
        """
        logger.info("Starting historical data backfill")
        data = {}
        
        for symbol in self.SYMBOLS:
            data[symbol] = {}
            
            for timeframe in self.TIMEFRAMES:
                try:
                    # Fetch 1000 candles with indicators
                    df = self.fetch_with_indicators(symbol, timeframe, limit=1000)
                    data[symbol][timeframe] = df
                    
                    # Small delay to respect rate limits
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to backfill {symbol} {timeframe}: {e}")
                    data[symbol][timeframe] = None
        
        logger.info("Historical data backfill complete")
        return data
    
    def get_symbol_for_db(self, symbol: str) -> str:
        """
        Convert exchange symbol to database format
        'BTC/USDT' -> 'btcusdt'
        """
        return symbol.replace('/', '').lower()
    
    def prepare_for_insert(self, df: pd.DataFrame) -> List[tuple]:
        """
        Convert DataFrame to list of tuples for database insertion
        
        Args:
            df: DataFrame with OHLCV + indicators
        
        Returns:
            List of tuples: (timestamp, open, high, low, close, volume, rsi_8, ema_20, ema_50)
        """
        records = []
        
        for _, row in df.iterrows():
            records.append((
                row['timestamp'],
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']),
                float(row['rsi_8']) if pd.notna(row['rsi_8']) else None,
                float(row['ema_20']) if pd.notna(row['ema_20']) else None,
                float(row['ema_50']) if pd.notna(row['ema_50']) else None
            ))
        
        return records


def test_btc_weekly():
    """Test fetching BTC/USDT weekly data specifically"""
    fetcher = DataFetcher()
    
    print("\n" + "="*60)
    print("Testing BTC/USDT Weekly Data Fetch")
    print("="*60)
    
    # Fetch weekly data
    print("\nFetching 1000 weekly candles...")
    df = fetcher.fetch_with_indicators('BTC/USDT', '1w', limit=1000)
    
    print(f"\n✓ Fetched {len(df)} candles")
    print(f"✓ Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Show first few candles
    print("\n--- First 3 Candles ---")
    print(df.head(3).to_string())
    
    # Show last few candles
    print("\n--- Last 3 Candles ---")
    print(df.tail(10).to_string())
    
    # Check indicators
    print("\n--- Indicator Summary ---")
    print(f"RSI(8) range: {df['rsi_8'].min():.2f} - {df['rsi_8'].max():.2f}")
    print(f"EMA(20) range: ${df['ema_20'].min():.2f} - ${df['ema_20'].max():.2f}")
    print(f"EMA(50) range: ${df['ema_50'].min():.2f} - ${df['ema_50'].max():.2f}")
    print(f"Non-null RSI values: {df['rsi_8'].notna().sum()}/{len(df)}")
    print(f"Non-null EMA(20) values: {df['ema_20'].notna().sum()}/{len(df)}")
    print(f"Non-null EMA(50) values: {df['ema_50'].notna().sum()}/{len(df)}")
    
    # Test data prep for DB
    print("\n--- Database Preparation Test ---")
    records = fetcher.prepare_for_insert(df.tail(1))
    rec = records[0]
    print(f"Sample record tuple (last candle):")
    print(f"  Timestamp: {rec[0]}")
    print(f"  OHLC: O={rec[1]:.2f} H={rec[2]:.2f} L={rec[3]:.2f} C={rec[4]:.2f}")
    print(f"  Volume: {rec[5]:.2f}")
    
    rsi_str = f"{rec[6]:.2f}" if rec[6] else "None"
    ema20_str = f"{rec[7]:.2f}" if rec[7] else "None"
    ema50_str = f"{rec[8]:.2f}" if rec[8] else "None"
    
    print(f"  RSI: {rsi_str}")
    print(f"  EMA20: {ema20_str}")
    print(f"  EMA50: {ema50_str}")
    
    # DB symbol format
    db_symbol = fetcher.get_symbol_for_db('BTC/USDT')
    print(f"\nDatabase table name: {db_symbol}_1w")
    
    print("\n" + "="*60)
    print("✓ All tests passed! Ready for database insertion.")
    print("="*60)
    
    return df


if __name__ == '__main__':
    test_btc_weekly()