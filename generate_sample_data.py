"""
Sample Data Generator for Backtesting Dashboard
Generates realistic 1-minute OHLCV data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(
    symbol='SAMPLE',
    start_date='2023-01-03 09:30:00',
    num_days=5,
    initial_price=100.0,
    volatility=0.02
):
    """
    Generate sample 1-minute stock data
    
    Parameters:
    -----------
    symbol : str
        Stock symbol
    start_date : str
        Starting date and time
    num_days : int
        Number of trading days
    initial_price : float
        Starting price
    volatility : float
        Price volatility (0.02 = 2%)
    
    Returns:
    --------
    DataFrame with OHLCV data
    """
    
    # Generate timestamps (6.5 hours per trading day, 1-min bars)
    minutes_per_day = 390  # 9:30 AM to 4:00 PM
    total_minutes = num_days * minutes_per_day
    
    start = pd.to_datetime(start_date)
    timestamps = []
    current = start
    
    for day in range(num_days):
        day_start = start + timedelta(days=day)
        for minute in range(minutes_per_day):
            timestamps.append(day_start + timedelta(minutes=minute))
    
    # Generate price data using geometric brownian motion
    np.random.seed(42)
    
    returns = np.random.normal(0, volatility, total_minutes)
    price_series = initial_price * np.exp(np.cumsum(returns))
    
    data = []
    
    for i, timestamp in enumerate(timestamps):
        # Generate OHLC with realistic relationships
        close = price_series[i]
        
        # High and low within reasonable range
        range_pct = abs(np.random.normal(0, volatility * 0.5))
        high = close * (1 + range_pct)
        low = close * (1 - range_pct)
        
        # Open is previous close (or close to it)
        if i == 0:
            open_price = initial_price
        else:
            open_price = price_series[i-1] * (1 + np.random.normal(0, volatility * 0.1))
        
        # Ensure OHLC relationships are valid
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume (higher at open/close, random throughout)
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Volume spikes at market open and close
        if (hour == 9 and minute < 45) or (hour == 15 and minute > 45):
            base_volume = np.random.randint(5000, 15000)
        else:
            base_volume = np.random.randint(1000, 5000)
        
        volume = base_volume + int(np.random.normal(0, base_volume * 0.3))
        volume = max(100, volume)  # Minimum volume
        
        # Trade count proportional to volume
        trade_count = max(1, int(volume / np.random.randint(50, 200)))
        
        # Calculate VWAP (simplified)
        vwap = (high + low + close) / 3
        
        data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S-05:00'),
            'symbol': symbol,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume,
            'trade_count': trade_count,
            'vwap': round(vwap, 2)
        })
    
    df = pd.DataFrame(data)
    return df


def add_trend(df, trend_strength=0.0005):
    """
    Add a trend to the data
    
    Parameters:
    -----------
    df : DataFrame
        Input data
    trend_strength : float
        Strength of trend (positive = uptrend, negative = downtrend)
    """
    df = df.copy()
    trend = np.arange(len(df)) * trend_strength
    
    df['open'] = df['open'] * (1 + trend)
    df['high'] = df['high'] * (1 + trend)
    df['low'] = df['low'] * (1 + trend)
    df['close'] = df['close'] * (1 + trend)
    df['vwap'] = df['vwap'] * (1 + trend)
    
    # Round to 2 decimals
    for col in ['open', 'high', 'low', 'close', 'vwap']:
        df[col] = df[col].round(2)
    
    return df


def add_patterns(df, pattern_frequency=0.1):
    """
    Add recognizable patterns to the data for testing strategies
    
    Parameters:
    -----------
    df : DataFrame
        Input data
    pattern_frequency : float
        Frequency of patterns (0.1 = 10% of bars)
    """
    df = df.copy()
    
    # Add some clear trends and reversals
    chunk_size = int(len(df) * pattern_frequency)
    
    for i in range(0, len(df) - chunk_size, chunk_size * 2):
        # Uptrend
        trend = np.linspace(0, 0.05, chunk_size)
        df.loc[i:i+chunk_size-1, 'close'] *= (1 + trend)
        
        # Downtrend
        if i + chunk_size * 2 < len(df):
            trend = np.linspace(0, -0.05, chunk_size)
            df.loc[i+chunk_size:i+chunk_size*2-1, 'close'] *= (1 + trend)
    
    return df


if __name__ == "__main__":
    """Generate sample data files"""
    
    print("Generating sample data files...")
    
    # 1. Basic sample data
    df1 = generate_sample_data(
        symbol='SAMPLE',
        num_days=5,
        initial_price=100.0,
        volatility=0.015
    )
    df1.to_csv('sample_data_basic.csv', index=False)
    print(f"✓ Created sample_data_basic.csv ({len(df1)} rows)")
    
    # 2. Trending data
    df2 = generate_sample_data(
        symbol='TREND',
        num_days=10,
        initial_price=150.0,
        volatility=0.02
    )
    df2 = add_trend(df2, trend_strength=0.0003)
    df2.to_csv('sample_data_trending.csv', index=False)
    print(f"✓ Created sample_data_trending.csv ({len(df2)} rows)")
    
    # 3. High volatility data
    df3 = generate_sample_data(
        symbol='VOLATILE',
        num_days=5,
        initial_price=50.0,
        volatility=0.04
    )
    df3.to_csv('sample_data_volatile.csv', index=False)
    print(f"✓ Created sample_data_volatile.csv ({len(df3)} rows)")
    
    # 4. Data with patterns
    df4 = generate_sample_data(
        symbol='PATTERNS',
        num_days=20,
        initial_price=200.0,
        volatility=0.02
    )
    df4 = add_patterns(df4, pattern_frequency=0.15)
    df4.to_csv('sample_data_patterns.csv', index=False)
    print(f"✓ Created sample_data_patterns.csv ({len(df4)} rows)")
    
    print("\nSample data generation complete!")
    print("\nYou can now use these files to test the backtesting dashboard.")
    print("\nRecommended test strategy: Simple Moving Average Crossover")
