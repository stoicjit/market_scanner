import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime

def fetch_and_analyze(symbol, timeframe, limit=200):
    """
    Fetch OHLCV data from Binance and calculate indicators
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle interval ('5m', '1h', '4h', '1d', '1w', '1M')
        limit: Number of candles to fetch
    
    Returns:
        DataFrame with OHLCV data and indicators
    """
    try:
        binance = ccxt.binance()
        
        print(f"\n📊 Fetching {symbol} {timeframe}")
        print("-" * 60)
        
        # Fetch OHLCV data
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate indicators
        df['rsi_14'] = ta.rsi(df['close'], length=8)
        df['ema_20'] = ta.ema(df['close'], length=14)
        df['ema_50'] = ta.ema(df['close'], length=50)
        
        # Display info
        print(f"✅ Fetched {len(df)} candles")
        print(f"📅 From: {df['timestamp'].iloc[0]}")
        print(f"📅 To:   {df['timestamp'].iloc[-1]}")
        
        # Weekly candle day check
        if timeframe == '1w':
            candle_day = df['timestamp'].iloc[-1].strftime('%A')
            print(f"🗓️  Weekly candle starts on: {candle_day}")
        
        # Show last 3 candles
        print(f"\n📈 Last 3 candles:")
        display_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'rsi_14', 'ema_20']
        print(df[display_cols].tail(3).to_string(index=False))
        
        # Additional stats
        print(f"\n💰 Volume: {df['volume'].iloc[-1]:,.2f}")
        if not pd.isna(df['rsi_14'].iloc[-1]):
            print(f"📊 RSI: {df['rsi_14'].iloc[-1]:.2f}")
        else:
            print(f"📊 RSI: None (needs more data)")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def check_available_symbols():
    """Check which of your target symbols are available on Binance"""
    
    print(f"\n{'='*70}")
    print("💱 SYMBOL AVAILABILITY CHECK")
    print(f"{'='*70}")
    
    try:
        binance = ccxt.binance()
        markets = binance.load_markets()
        
        # Your target symbols (using USDT since Binance doesn't have USD pairs)
        target_symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'XRP/USDT', 
                         'DOGE/USDT', 'DOT/USDT', 'ADA/USDT']
        
        print("\n🟡 Binance USDT Pairs:")
        available = []
        for symbol in target_symbols:
            if symbol in markets:
                print(f"  ✅ {symbol}")
                available.append(symbol)
            else:
                print(f"  ❌ {symbol}")
        
        return available
        
    except Exception as e:
        print(f"❌ Error loading markets: {e}")
        return []


def test_all_timeframes(symbol='BTC/USDT'):
    """Test all required timeframes for a symbol"""
    
    print(f"\n{'='*70}")
    print(f"⏱️  TESTING ALL TIMEFRAMES - {symbol}")
    print(f"{'='*70}")
    
    timeframes = ['5m', '1h', '4h', '1d', '1w', '1M']
    results = {}
    
    for tf in timeframes:
        df = fetch_and_analyze(symbol, tf, limit=200)
        if df is not None:
            results[tf] = df
    
    return results


def test_multiple_symbols(symbols, timeframe='1h'):
    """Test a specific timeframe across multiple symbols"""
    
    print(f"\n{'='*70}")
    print(f"📊 TESTING {timeframe} ACROSS MULTIPLE SYMBOLS")
    print(f"{'='*70}")
    
    results = {}
    for symbol in symbols:
        df = fetch_and_analyze(symbol, timeframe, limit=100)
        if df is not None:
            results[symbol] = df
    
    return results


if __name__ == "__main__":
    print("🚀 Binance Data Quality Test\n")
    
    # 1. Check available symbols
    available_symbols = check_available_symbols()
    
    # 2. Test all timeframes on BTC/USDT
    print(f"\n{'='*70}")
    print("🧪 FULL TIMEFRAME TEST (BTC/USDT)")
    print(f"{'='*70}")
    btc_results = test_all_timeframes('BTC/USDT')
    
    # 3. Test 1h across your other symbols
    if len(available_symbols) > 1:
        other_symbols = available_symbols[1:4]  # Test 3 more symbols
        symbol_results = test_multiple_symbols(other_symbols, '1h')
    
    # 4. Summary
    print(f"\n{'='*70}")
    print("✨ TEST SUMMARY")
    print(f"{'='*70}")
    
    if btc_results:
        print(f"\n✅ BTC/USDT - Successfully fetched {len(btc_results)} timeframes:")
        for tf in btc_results.keys():
            print(f"  ✓ {tf}")
    
    print("\n📝 Next Steps:")
    print("  1. Compare RSI values with TradingView (minor differences are okay)")
    print("  2. Verify weekly starts on Monday")
    print("  3. Check volume accuracy")
    print("  4. Ready to integrate into your scanner!")
    
    print(f"\n💡 Rate Limit Info:")
    print("  Binance allows ~1200 requests/minute")
    print("  Your scanner will use ~7-15 requests per cycle")
    print("  You're well within limits!")