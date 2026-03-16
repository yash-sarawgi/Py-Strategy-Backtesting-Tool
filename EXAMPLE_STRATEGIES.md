# Example Trading Strategies for Backtesting Dashboard

## Strategy 1: EMA Crossover with Volume Confirmation
```python
# Calculate EMAs
df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
df['Volume_MA'] = df['volume'].rolling(window=20).mean()

signals = []
position = 0

for i in range(26, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    ema_12 = df['EMA_12'].iloc[i]
    ema_26 = df['EMA_26'].iloc[i]
    ema_12_prev = df['EMA_12'].iloc[i-1]
    ema_26_prev = df['EMA_26'].iloc[i-1]
    volume = df['volume'].iloc[i]
    volume_ma = df['Volume_MA'].iloc[i]
    
    # Buy on bullish crossover with volume confirmation
    if ema_12_prev <= ema_26_prev and ema_12 > ema_26 and volume > volume_ma and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell on bearish crossover
    elif ema_12_prev >= ema_26_prev and ema_12 < ema_26 and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0
```

## Strategy 2: MACD with RSI Filter
```python
# Calculate MACD
df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
df['MACD'] = df['EMA_12'] - df['EMA_26']
df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

# Calculate RSI
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['RSI'] = calculate_rsi(df['close'])

signals = []
position = 0

for i in range(30, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    macd = df['MACD'].iloc[i]
    signal_line = df['Signal_Line'].iloc[i]
    macd_prev = df['MACD'].iloc[i-1]
    signal_prev = df['Signal_Line'].iloc[i-1]
    rsi = df['RSI'].iloc[i]
    
    # Buy when MACD crosses above signal and RSI not overbought
    if macd_prev <= signal_prev and macd > signal_line and rsi < 70 and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell when MACD crosses below signal or RSI oversold
    elif ((macd_prev >= signal_prev and macd < signal_line) or rsi > 80) and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0
```

## Strategy 3: Support/Resistance Breakout
```python
# Calculate rolling highs and lows
lookback = 20
df['Resistance'] = df['high'].rolling(window=lookback).max()
df['Support'] = df['low'].rolling(window=lookback).min()
df['ATR'] = (df['high'] - df['low']).rolling(window=14).mean()

signals = []
position = 0

for i in range(lookback, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    resistance = df['Resistance'].iloc[i-1]  # Previous resistance
    support = df['Support'].iloc[i-1]  # Previous support
    atr = df['ATR'].iloc[i]
    
    # Buy on resistance breakout with strong move
    if price > resistance and (price - resistance) > atr * 0.5 and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell on support break or take profit at 2*ATR
    elif position == 1:
        entry_price = signals[-1]['price']
        if price < support or (price - entry_price) > atr * 2:
            signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
            position = 0
```

## Strategy 4: Mean Reversion with Z-Score
```python
# Calculate z-score
period = 20
df['SMA'] = df['close'].rolling(window=period).mean()
df['STD'] = df['close'].rolling(window=period).std()
df['Z_Score'] = (df['close'] - df['SMA']) / df['STD']

signals = []
position = 0
z_threshold = 2.0

for i in range(period, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    z_score = df['Z_Score'].iloc[i]
    
    # Buy when oversold (z-score < -2)
    if z_score < -z_threshold and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell when returns to mean or overbought
    elif (z_score > -0.5 or z_score > z_threshold) and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0
```

## Strategy 5: Momentum with Stop Loss and Take Profit
```python
# Calculate momentum
df['ROC'] = df['close'].pct_change(periods=10) * 100
df['Volume_MA'] = df['volume'].rolling(window=20).mean()

signals = []
position = 0
stop_loss_pct = 2.0  # 2% stop loss
take_profit_pct = 4.0  # 4% take profit

for i in range(20, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    roc = df['ROC'].iloc[i]
    volume = df['volume'].iloc[i]
    volume_ma = df['Volume_MA'].iloc[i]
    
    # Buy on strong momentum with volume
    if roc > 3 and volume > volume_ma * 1.5 and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell on stop loss or take profit
    elif position == 1:
        entry_price = signals[-1]['price']
        pnl_pct = ((price - entry_price) / entry_price) * 100
        
        if pnl_pct <= -stop_loss_pct or pnl_pct >= take_profit_pct:
            signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
            position = 0
```

## Strategy 6: Price Action Patterns
```python
# Identify candlestick patterns
df['Body'] = abs(df['close'] - df['open'])
df['Upper_Shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
df['Lower_Shadow'] = df[['open', 'close']].min(axis=1) - df['low']
df['ATR'] = (df['high'] - df['low']).rolling(window=14).mean()

signals = []
position = 0

for i in range(15, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    body = df['Body'].iloc[i]
    upper_shadow = df['Upper_Shadow'].iloc[i]
    lower_shadow = df['Lower_Shadow'].iloc[i]
    atr = df['ATR'].iloc[i]
    
    # Bullish hammer pattern (long lower shadow, small body)
    is_hammer = (lower_shadow > body * 2) and (upper_shadow < body * 0.5)
    
    # Buy on hammer pattern
    if is_hammer and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Exit after 10 bars or 1.5*ATR move
    elif position == 1:
        entry_price = signals[-1]['price']
        bars_held = i - df.index.get_loc(signals[-1]['timestamp'])
        
        if bars_held >= 10 or abs(price - entry_price) >= atr * 1.5:
            signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
            position = 0
```

## Strategy 7: Multi-Timeframe Confluence
```python
# Simulate multiple timeframes using different periods
df['Fast_MA'] = df['close'].rolling(window=10).mean()
df['Medium_MA'] = df['close'].rolling(window=30).mean()
df['Slow_MA'] = df['close'].rolling(window=50).mean()

signals = []
position = 0

for i in range(50, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    fast_ma = df['Fast_MA'].iloc[i]
    medium_ma = df['Medium_MA'].iloc[i]
    slow_ma = df['Slow_MA'].iloc[i]
    
    # Buy when all MAs aligned bullish
    if fast_ma > medium_ma > slow_ma and position == 0:
        # Additional confirmation: price above all MAs
        if price > fast_ma:
            signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
            position = 1
    
    # Sell when alignment breaks
    elif (fast_ma < medium_ma or medium_ma < slow_ma) and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0
```

## Strategy 8: Opening Range Breakout
```python
# Identify first 15 minutes (15 bars for 1-min data)
df['Time'] = df.index.time
df['Date'] = df.index.date

signals = []
position = 0
opening_range = {}

for i in range(1, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    current_date = df['Date'].iloc[i]
    current_time = df['Time'].iloc[i]
    
    # Reset on new day
    if current_date not in opening_range:
        opening_range[current_date] = {
            'high': df['high'].iloc[i],
            'low': df['low'].iloc[i],
            'range_set': False
        }
    
    # Build opening range (first 15 minutes)
    if i < 15 or not opening_range[current_date]['range_set']:
        opening_range[current_date]['high'] = max(opening_range[current_date]['high'], df['high'].iloc[i])
        opening_range[current_date]['low'] = min(opening_range[current_date]['low'], df['low'].iloc[i])
        if i >= 15:
            opening_range[current_date]['range_set'] = True
        continue
    
    # Trade breakouts
    or_high = opening_range[current_date]['high']
    or_low = opening_range[current_date]['low']
    
    # Buy on breakout above opening range high
    if price > or_high and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell if breaks back below range or end of day
    elif position == 1 and (price < or_low or current_time.hour >= 15):
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0
```

## Tips for Using These Strategies

1. **Understand the Logic**: Don't blindly copy - understand what each strategy does
2. **Adjust Parameters**: Tune lookback periods, thresholds based on your data
3. **Combine Strategies**: Mix elements from different strategies
4. **Risk Management**: Always include stop losses and position sizing
5. **Test Different Markets**: What works for one stock may not work for another
6. **Avoid Overfitting**: Don't optimize too much on historical data

## Common Indicator Functions

### RSI Calculator
```python
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

### ATR Calculator
```python
def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr
```

### Stochastic Oscillator
```python
def calculate_stochastic(df, period=14):
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    k = 100 * (df['close'] - low_min) / (high_max - low_min)
    d = k.rolling(window=3).mean()
    return k, d
```

Remember: Past performance doesn't guarantee future results. Always backtest thoroughly!
