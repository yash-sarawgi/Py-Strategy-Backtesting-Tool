# 🔧 Troubleshooting Guide

Common errors and their solutions for the Backtesting Dashboard.

## Error: KeyError: 'timestamp'

### Problem
```
KeyError: 'timestamp'
Traceback (most recent call last):
  File "...", line 167, in execute_strategy
    df['timestamp'] = pd.to_datetime(df['timestamp'])
```

### Solutions

1. **Check CSV Column Names**
   - Open your CSV in a text editor or Excel
   - Verify the first column is named exactly `timestamp` (case-sensitive)
   - Common variations: `Timestamp`, `time`, `Time`, `datetime`

2. **Use Preview Data Button**
   - Click "Preview Data" after loading CSV
   - Check the actual column names shown
   - The app will auto-detect common timestamp column names

3. **Fix CSV Headers**
   If your CSV has different column names, either:
   - Rename the column to `timestamp` in your CSV, OR
   - The app now auto-detects common variations

### Example Fix
If your CSV looks like this:
```csv
Time,Symbol,Open,High,Low,Close,Volume
2020-11-30 09:41:00,SOFI,11,11,11,11,100
```

Change to:
```csv
timestamp,symbol,open,high,low,close,volume
2020-11-30 09:41:00,SOFI,11,11,11,11,100
```

**OR** the updated app will automatically detect `Time` as the timestamp column!

---

## Error: No signals generated

### Problem
```
ValueError: No signals generated. Make sure your strategy appends to 'signals' list.
```

### Causes & Solutions

1. **Not Appending to signals List**
   ```python
   # ❌ WRONG
   if buy_condition:
       position = 1
   
   # ✅ CORRECT
   if buy_condition and position == 0:
       signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
       position = 1
   ```

2. **Conditions Never Met**
   Your buy/sell conditions might be too strict. Debug with print statements:
   ```python
   if buy_condition:
       print(f"Buy signal at {timestamp}, price={price}")
       signals.append(...)
   ```

3. **Wrong Loop Range**
   ```python
   # ❌ WRONG - not enough data for indicators
   for i in range(0, len(df)):
   
   # ✅ CORRECT - start after indicator period
   for i in range(50, len(df)):  # If using 50-period SMA
   ```

4. **Position Tracking Error**
   ```python
   # ❌ WRONG - can buy when already in position
   if buy_condition:
       signals.append(...)
   
   # ✅ CORRECT - check position first
   if buy_condition and position == 0:
       signals.append(...)
       position = 1
   ```

---

## Error: IndexError / KeyError with iloc

### Problem
```
IndexError: single positional indexer is out-of-bounds
KeyError: 'close'
```

### Solutions

1. **Start Loop After Indicator Period**
   ```python
   # Calculate 50-period SMA
   df['SMA_50'] = df['close'].rolling(window=50).mean()
   
   # ❌ WRONG
   for i in range(0, len(df)):  # SMA is NaN for first 50 rows!
   
   # ✅ CORRECT
   for i in range(50, len(df)):  # Start after SMA is valid
   ```

2. **Use Correct Indexing**
   ```python
   # ✅ CORRECT - use iloc for integer position
   price = df['close'].iloc[i]
   
   # ❌ WRONG - don't use loc with integer
   price = df['close'].loc[i]
   ```

3. **Check Column Names**
   ```python
   # If your CSV has 'Close' (capital C)
   print(df.columns)  # Check actual names
   
   # Either use exact name:
   price = df['Close'].iloc[i]
   
   # Or rename columns:
   df.columns = df.columns.str.lower()
   ```

---

## Error: Data Not Loading / Empty Results

### Problem
- CSV loads but no data shown
- Backtest runs but no trades

### Solutions

1. **Check CSV Format**
   Required minimum columns:
   - `timestamp` (or similar)
   - `close` (or `Close`)
   
   Example valid CSV:
   ```csv
   timestamp,symbol,open,high,low,close,volume
   2020-11-30 09:41:00,SOFI,11,11,11,11,100
   2020-11-30 09:42:00,SOFI,11.5,11.5,11.5,11.5,200
   ```

2. **Verify Date Format**
   Acceptable timestamp formats:
   - `2020-11-30 09:41:00`
   - `2020-11-30 09:41:00-05:00`
   - `11/30/2020 09:41:00`
   
   pandas will auto-detect most formats.

3. **Check Data Volume**
   - Need enough data for your indicators
   - Example: 50-period SMA needs at least 50 rows
   - Try with at least 100+ rows of data

---

## Error: Strategy Runs Slowly

### Problem
Backtest takes too long to complete

### Solutions

1. **Vectorize When Possible**
   ```python
   # ❌ SLOW - loop for calculations
   for i in range(len(df)):
       df.loc[i, 'SMA'] = df['close'].iloc[i-20:i].mean()
   
   # ✅ FAST - vectorized operation
   df['SMA'] = df['close'].rolling(window=20).mean()
   ```

2. **Reduce Data Size for Testing**
   ```python
   # Test on smaller subset first
   df_test = df.head(500)  # First 500 rows
   ```

3. **Optimize Indicator Calculations**
   - Calculate once before loop, not inside loop
   - Use built-in pandas functions

---

## Error: NaN Values in Indicators

### Problem
```
RuntimeWarning: invalid value encountered
NaN values in calculations
```

### Solutions

1. **Handle NaN in Conditions**
   ```python
   # ✅ Check for NaN
   if not pd.isna(sma_20) and sma_20 > sma_50:
       # Trade logic
   ```

2. **Drop NaN Rows**
   ```python
   df['SMA'] = df['close'].rolling(20).mean()
   df = df.dropna()  # Remove rows with NaN
   ```

3. **Forward Fill**
   ```python
   df['SMA'] = df['close'].rolling(20).mean().fillna(method='ffill')
   ```

---

## General Debugging Tips

### 1. Use Print Statements
```python
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"First row: {df.iloc[0]}")
print(f"Total signals: {len(signals)}")
```

### 2. Test Strategy Step-by-Step
```python
# Test indicator calculation
df['SMA_20'] = df['close'].rolling(20).mean()
print(df[['close', 'SMA_20']].tail())

# Test signal generation
signals = []
for i in range(50, min(100, len(df))):  # Test first 50 iterations
    # Your logic here
    pass
print(f"Signals generated: {len(signals)}")
```

### 3. Use Sample Data
Generate test data first:
```bash
python generate_sample_data.py
```
Test your strategy on this known-good data.

### 4. Preview Your Data
Always click "Preview Data" button after loading CSV to verify:
- Column names are correct
- Data types are appropriate
- Timestamps are parsed correctly
- Values look reasonable

### 5. Check the Logs
The application shows errors in popup dialogs. Read them carefully - they often tell you exactly what's wrong!

---

## Quick Fixes Checklist

When something doesn't work, check these in order:

- [ ] Is my CSV loaded? (Check file path shown)
- [ ] Do I have a 'timestamp' column?
- [ ] Do I have a 'close' column?
- [ ] Does my loop start after the longest indicator period?
- [ ] Am I using `iloc[i]` for indexing?
- [ ] Am I appending to the `signals` list?
- [ ] Is my signal format correct? `{'timestamp': ts, 'type': 'BUY', 'price': p}`
- [ ] Am I tracking position correctly? (0 or 1)
- [ ] Have I used "Preview Data" to verify my CSV?

---

## Getting Help

If you're still stuck:

1. **Check the error message carefully** - it usually tells you the exact problem
2. **Use "Preview Data"** to inspect your CSV
3. **Try the default strategy** on sample data first
4. **Test with sample data** from generate_sample_data.py
5. **Simplify your strategy** - remove complex logic temporarily
6. **Add print statements** to debug step by step

---

## Common Strategy Issues

### Issue: Trades Never Close
**Problem:** Position = 1 but never sell
**Fix:** Make sure you have a sell condition
```python
if position == 1:
    # Must have SOME way to exit!
    if sell_condition:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0
```

### Issue: Too Many Trades
**Problem:** Entering/exiting constantly
**Fix:** Add filters or holding period
```python
bars_since_entry = 0
if position == 1:
    bars_since_entry += 1
    # Only exit after minimum holding period
    if bars_since_entry >= 5 and sell_condition:
        signals.append(...)
```

### Issue: No Trades at All
**Problem:** Conditions too strict
**Fix:** Relax thresholds or check data
```python
# Too strict - might never trigger
if rsi < 10:  # RSI rarely goes below 10

# More reasonable
if rsi < 30:  # Commonly oversold level
```

---

## Need More Help?

- Check `README.md` for complete documentation
- See `EXAMPLE_STRATEGIES.md` for working examples
- Use Help → Quick Reference in the app
- Use Help → Example Strategies in the app

Remember: Start simple, test often, and build complexity gradually!
