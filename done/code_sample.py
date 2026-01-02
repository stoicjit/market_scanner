import ccxt
import pandas as pd
import pandas_ta as ta

binance = ccxt.kucoin()
ohlcv = binance.fetch_ohlcv('XMR/USDT', '15m', limit=200)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# Calculate RSI
df['rsi_8'] = ta.rsi(df['close'], length=8)

# Show last value
print(f"Our RSI: {df['rsi_8'].iloc[-1]:.2f}")
print(f"BTC Close: {df['close'].iloc[-1]:.2f}")