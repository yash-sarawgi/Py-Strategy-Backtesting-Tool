"""
Advanced Backtesting Dashboard with GUI
Features: Strategy execution, comprehensive metrics, trade analysis, visualizations
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import seaborn as sns
from datetime import datetime, time
import json
import traceback
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("darkgrid")
plt.style.use('seaborn-v0_8-darkgrid')


class BacktestEngine:
    """Core backtesting engine with comprehensive analytics"""
    
    def __init__(self, data, strategy_code, initial_capital=100000):
        self.data = data.copy()
        self.strategy_code = strategy_code
        self.initial_capital = initial_capital
        self.trades = []
        self.positions = []
        self.equity_curve = []
        self.metrics = {}
        
    def execute_strategy(self):
        """Execute the user's strategy code"""
        try:
            # Prepare data
            df = self.data.copy()
            
            # Find timestamp column (handle various naming conventions)
            timestamp_col = None
            possible_names = ['timestamp', 'Timestamp', 'time', 'Time', 'datetime', 'DateTime', 'date']
            
            for col in df.columns:
                if col.lower().strip() in [name.lower() for name in possible_names]:
                    timestamp_col = col
                    break
            
            if timestamp_col is None:
                # If no timestamp column found, use the first column
                timestamp_col = df.columns[0]
                print(f"Warning: No timestamp column found. Using first column: '{timestamp_col}'")
            
            # Convert to datetime and set as index
            df['timestamp'] = pd.to_datetime(df[timestamp_col], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(None)

            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Initialize tracking variables
            position = 0  # 0: no position, 1: long, -1: short
            entry_price = 0
            entry_time = None
            capital = self.initial_capital
            shares = 0
            
            # Create strategy namespace
            namespace = {
                'df': df,
                'pd': pd,
                'np': np,
                'position': position,
                'entry_price': entry_price,
                'capital': capital,
                'shares': shares,
                'trades': [],
                'signals': []
            }
            
            # Execute user's strategy code
            exec(self.strategy_code, namespace)
            
            # Extract signals from namespace
            signals = namespace.get('signals', [])
            
            if not signals:
                raise ValueError("No signals generated. Make sure your strategy appends to 'signals' list.")
            
            # Validate signal format
            for idx, signal in enumerate(signals):
                if not isinstance(signal, dict):
                    raise ValueError(f"Signal {idx} is not a dictionary. Each signal must be: {{'timestamp': ts, 'type': 'BUY'/'SELL', 'price': float}}")
                
                required_keys = ['timestamp', 'type', 'price']
                missing_keys = [key for key in required_keys if key not in signal]
                if missing_keys:
                    raise ValueError(f"Signal {idx} missing required keys: {missing_keys}. Required format: {{'timestamp': ts, 'type': 'BUY'/'SELL', 'price': float}}")
                
                if signal['type'] not in ['BUY', 'SELL']:
                    raise ValueError(f"Signal {idx} has invalid type '{signal['type']}'. Must be 'BUY' or 'SELL'.")
            
            print(f"Generated {len(signals)} signals")
            
            # Process signals and generate trades
            for signal in signals:
                # Ensure timestamp is a pandas Timestamp
                timestamp = pd.Timestamp(signal['timestamp'])
                signal_type = signal['type']  # 'BUY' or 'SELL'
                price = float(signal['price'])
                
                if signal_type == 'BUY' and position == 0:
                    # Enter long position
                    shares = capital / price
                    entry_price = price
                    entry_time = timestamp
                    position = 1
                    
                elif signal_type == 'SELL' and position == 1:
                    # Exit long position
                    exit_price = price
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                    capital += pnl
                    
                    # Calculate duration
                    try:
                        duration_minutes = (timestamp - entry_time).total_seconds() / 60
                    except:
                        duration_minutes = 0
                    
                    trade = {
                        'entry_time': entry_time,
                        'exit_time': timestamp,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'shares': shares,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'duration': duration_minutes,
                        'capital_after': capital
                    }
                    self.trades.append(trade)
                    position = 0
                    shares = 0
            
            # Calculate equity curve
            self._calculate_equity_curve()
            
            # Calculate metrics
            self._calculate_metrics()
            
            return True
            
        except Exception as e:
            raise Exception(f"Strategy execution error: {str(e)}\n{traceback.format_exc()}")
    
    def _calculate_equity_curve(self):
        """Calculate equity curve over time"""
        if not self.trades:
            return
        
        equity = self.initial_capital
        
        # Get the first timestamp from data
        try:
            first_timestamp = pd.Timestamp(self.data.iloc[0]['timestamp']) if 'timestamp' in self.data.columns else pd.Timestamp(self.data.index[0])
        except:
            first_timestamp = pd.Timestamp.now()
        
        self.equity_curve = [{'timestamp': first_timestamp, 'equity': equity}]
        
        for trade in self.trades:
            equity = trade['capital_after']
            exit_time = pd.Timestamp(trade['exit_time'])
            self.equity_curve.append({
                'timestamp': exit_time,
                'equity': equity
            })
    
    def _calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            self.metrics = {'error': 'No trades executed'}
            return
        
        trades_df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        total_return = ((self.equity_curve[-1]['equity'] - self.initial_capital) / self.initial_capital) * 100
        
        # Win/Loss metrics
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        largest_win = winning_trades['pnl'].max() if len(winning_trades) > 0 else 0
        largest_loss = losing_trades['pnl'].min() if len(losing_trades) > 0 else 0
        
        # Risk metrics
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else np.inf
        
        # Drawdown calculation
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdowns.min()
        
        # Sharpe ratio (simplified - assumes daily data)
        returns = trades_df['pnl_pct']
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        
        # Time-based analysis
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
        
        try:
            trades_df['entry_hour'] = trades_df['entry_time'].dt.hour
            trades_df['entry_day'] = trades_df['entry_time'].dt.day_name()
        except Exception as e:
            print(f"Warning: Could not extract time features: {e}")
            trades_df['entry_hour'] = 0
            trades_df['entry_day'] = 'Unknown'
        
        # Average trade duration
        avg_duration = trades_df['duration'].mean()
        
        # Consecutive wins/losses
        trades_df['win'] = trades_df['pnl'] > 0
        trades_df['streak'] = (trades_df['win'] != trades_df['win'].shift()).cumsum()
        streak_lengths = trades_df.groupby('streak')['win'].agg(['first', 'count'])
        max_consecutive_wins = streak_lengths[streak_lengths['first'] == True]['count'].max() if len(streak_lengths[streak_lengths['first'] == True]) > 0 else 0
        max_consecutive_losses = streak_lengths[streak_lengths['first'] == False]['count'].max() if len(streak_lengths[streak_lengths['first'] == False]) > 0 else 0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * abs(avg_loss))
        
        self.metrics = {
            # Summary
            'Total Trades': total_trades,
            'Winning Trades': len(winning_trades),
            'Losing Trades': len(losing_trades),
            'Win Rate (%)': round(win_rate, 2),
            
            # Returns
            'Total P&L ($)': round(total_pnl, 2),
            'Total Return (%)': round(total_return, 2),
            'Final Capital ($)': round(self.equity_curve[-1]['equity'], 2),
            
            # Win/Loss Stats
            'Average Win ($)': round(avg_win, 2),
            'Average Loss ($)': round(avg_loss, 2),
            'Largest Win ($)': round(largest_win, 2),
            'Largest Loss ($)': round(largest_loss, 2),
            'Avg Win (%)': round(winning_trades['pnl_pct'].mean(), 2) if len(winning_trades) > 0 else 0,
            'Avg Loss (%)': round(losing_trades['pnl_pct'].mean(), 2) if len(losing_trades) > 0 else 0,
            
            # Risk Metrics
            'Profit Factor': round(profit_factor, 2) if profit_factor != np.inf else 'Inf',
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Expectancy ($)': round(expectancy, 2),
            
            # Trade Characteristics
            'Avg Trade Duration (min)': round(avg_duration, 2),
            'Max Consecutive Wins': int(max_consecutive_wins),
            'Max Consecutive Losses': int(max_consecutive_losses),
        }
        
        # Store for detailed analysis
        self.trades_df = trades_df


class BacktestingDashboard:
    """Main GUI application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Backtesting Dashboard")
        self.root.geometry("1600x900")
        
        # Variables
        self.csv_path = tk.StringVar()
        self.initial_capital = tk.DoubleVar(value=100000)
        self.data = None
        self.backtest_engine = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Reference", command=self.show_quick_reference)
        help_menu.add_command(label="Example Strategies", command=self.show_examples)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Strategy input
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        # Right panel - Results
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)
        
        # === LEFT PANEL ===
        
        # File selection
        file_frame = ttk.LabelFrame(left_panel, text="Data Selection", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_frame, text="Select CSV File", command=self.select_file).pack(fill=tk.X, pady=2)
        ttk.Label(file_frame, textvariable=self.csv_path, wraplength=400).pack(fill=tk.X, pady=2)
        
        # View Data button
        ttk.Button(file_frame, text="Preview Data", command=self.preview_data).pack(fill=tk.X, pady=2)
        
        # Capital input
        capital_frame = ttk.Frame(file_frame)
        capital_frame.pack(fill=tk.X, pady=5)
        ttk.Label(capital_frame, text="Initial Capital ($):").pack(side=tk.LEFT)
        ttk.Entry(capital_frame, textvariable=self.initial_capital, width=15).pack(side=tk.LEFT, padx=5)
        
        # Strategy code editor
        code_frame = ttk.LabelFrame(left_panel, text="Strategy Code", padding=10)
        code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Instructions
        instructions = """# Strategy Instructions:
# 1. Use 'df' to access the data (pandas DataFrame)
# 2. Generate signals and append to 'signals' list
# 3. Each signal: {'timestamp': timestamp, 'type': 'BUY'/'SELL', 'price': price}
#
# Example Strategy:"""
        
        ttk.Label(code_frame, text=instructions, font=('Courier', 9), justify=tk.LEFT).pack(anchor=tk.W)
        
        self.code_editor = scrolledtext.ScrolledText(code_frame, height=25, font=('Courier', 10))
        self.code_editor.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Default strategy example
        default_strategy = """
# Simple Moving Average Crossover Strategy
# Note: Data is already indexed by timestamp

# Calculate moving averages on the 'close' column
df['SMA_20'] = df['close'].rolling(window=20).mean()
df['SMA_50'] = df['close'].rolling(window=50).mean()

signals = []
position = 0

# Start after we have enough data for indicators (50 periods)
for i in range(50, len(df)):
    timestamp = df.index[i]  # Timestamp is the index
    price = df['close'].iloc[i]
    sma_20 = df['SMA_20'].iloc[i]
    sma_50 = df['SMA_50'].iloc[i]
    sma_20_prev = df['SMA_20'].iloc[i-1]
    sma_50_prev = df['SMA_50'].iloc[i-1]
    
    # Buy signal: SMA 20 crosses above SMA 50
    if sma_20_prev <= sma_50_prev and sma_20 > sma_50 and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    
    # Sell signal: SMA 20 crosses below SMA 50
    elif sma_20_prev >= sma_50_prev and sma_20 < sma_50 and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0

# Important: signals list must contain entries like:
# {'timestamp': <datetime>, 'type': 'BUY'/'SELL', 'price': <float>}
"""
        self.code_editor.insert('1.0', default_strategy)
        
        # Run button
        ttk.Button(left_panel, text="Run Backtest", command=self.run_backtest, 
                  style='Accent.TButton').pack(fill=tk.X, padx=5, pady=10)
        
        # === RIGHT PANEL ===
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Summary Metrics
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Summary Metrics")
        
        # Tab 2: Equity Curve
        self.equity_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.equity_tab, text="Equity Curve")
        
        # Tab 3: Trade Analysis
        self.trades_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.trades_tab, text="Trade Analysis")
        
        # Tab 4: Time Analysis
        self.time_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.time_tab, text="Time Analysis")
        
        # Tab 5: Distribution Analysis
        self.dist_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dist_tab, text="Distribution Analysis")
        
        # Tab 6: Detailed Trades
        self.detail_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.detail_tab, text="Trade Details")
        
    def select_file(self):
        """Select CSV file"""
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path.set(filename)
            try:
                self.data = pd.read_csv(filename)
                
                # Normalize column names (strip whitespace)
                self.data.columns = self.data.columns.str.strip()
                
                # Try to identify and convert timestamp column
                timestamp_col = None
                possible_names = ['timestamp', 'Timestamp', 'time', 'Time', 'datetime', 'DateTime', 'date', 'Date']
                
                for col in self.data.columns:
                    if col in possible_names or col.lower() in [n.lower() for n in possible_names]:
                        timestamp_col = col
                        break
                
                if timestamp_col:
                    try:
                        # Try to convert to datetime
                        self.data[timestamp_col] = pd.to_datetime(self.data[timestamp_col], utc=True)
                        self.data[timestamp_col] = self.data[timestamp_col].dt.tz_convert(None)

                        print(f"✓ Timestamp column '{timestamp_col}' converted to datetime")
                    except Exception as e:
                        print(f"Warning: Could not convert '{timestamp_col}' to datetime: {e}")
                else:
                    # Try first column
                    try:
                        self.data[self.data.columns[0]] = pd.to_datetime(self.data[self.data.columns[0]])
                        print(f"✓ First column '{self.data.columns[0]}' converted to datetime")
                    except:
                        print("Warning: No timestamp column detected")
                
                # Check for required columns (case-insensitive)
                col_lower = [col.lower() for col in self.data.columns]
                
                if 'close' not in col_lower:
                    messagebox.showwarning(
                        "Warning", 
                        f"No 'close' column found!\n"
                        f"Available columns: {', '.join(self.data.columns)}\n\n"
                        "Your strategy will need to use the exact column names shown above."
                    )
                
                messagebox.showinfo(
                    "Success", 
                    f"✓ Loaded {len(self.data)} rows\n"
                    f"✓ {len(self.data.columns)} columns: {', '.join(self.data.columns[:5])}{'...' if len(self.data.columns) > 5 else ''}\n\n"
                    "Click 'Preview Data' to verify."
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV:\n{str(e)}")
                self.data = None
    
    def preview_data(self):
        """Preview the loaded data"""
        if self.data is None:
            messagebox.showwarning("No Data", "Please select a CSV file first")
            return
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Data Preview")
        preview_window.geometry("900x400")
        
        # Add text widget with scrollbar
        frame = ttk.Frame(preview_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = scrolledtext.ScrolledText(frame, font=('Courier', 9))
        text.pack(fill=tk.BOTH, expand=True)
        
        # Show data info
        info = f"Data Shape: {self.data.shape[0]} rows × {self.data.shape[1]} columns\n"
        info += f"Columns: {', '.join(self.data.columns)}\n"
        info += "=" * 80 + "\n\n"
        info += "First 10 rows:\n"
        info += "=" * 80 + "\n"
        info += self.data.head(10).to_string()
        info += "\n\n" + "=" * 80 + "\n"
        info += "Data Types:\n"
        info += "=" * 80 + "\n"
        info += str(self.data.dtypes)
        
        text.insert('1.0', info)
        text.config(state='disabled')  # Make read-only
    
    def run_backtest(self):
        """Execute backtest"""
        if self.data is None:
            messagebox.showerror("Error", "Please select a CSV file first")
            return
        
        strategy_code = self.code_editor.get('1.0', tk.END)
        
        if not strategy_code.strip():
            messagebox.showerror("Error", "Please enter strategy code")
            return
        
        try:
            # Show progress
            self.root.config(cursor="wait")
            self.root.update()
            
            # Run backtest
            self.backtest_engine = BacktestEngine(
                self.data,
                strategy_code,
                self.initial_capital.get()
            )
            
            success = self.backtest_engine.execute_strategy()
            
            if success:
                self.display_results()
                messagebox.showinfo("Success", "Backtest completed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Backtest failed:\n{str(e)}")
            
            # Show troubleshooting tips
            error_msg = str(e).lower()
            tips = []
            
            if 'timestamp' in error_msg or 'keyerror' in error_msg:
                tips.append("• Check that your CSV has a 'timestamp' column")
                tips.append("• Use 'Preview Data' button to verify column names")
                tips.append("• Ensure timestamp format is readable (e.g., '2020-11-30 09:41:00')")
            
            if 'close' in error_msg:
                tips.append("• Check that your CSV has 'open', 'high', 'low', 'close' columns")
                tips.append("• Column names are case-sensitive")
            
            if 'signals' in error_msg or 'no signals' in error_msg:
                tips.append("• Make sure you're appending to the 'signals' list")
                tips.append("• Check your buy/sell conditions are being met")
                tips.append("• Verify your strategy logic with print statements")
            
            if 'index' in error_msg or 'iloc' in error_msg:
                tips.append("• Check your loop range (e.g., start after indicator period)")
                tips.append("• Use iloc[i] for integer indexing")
            
            if tips:
                tip_window = tk.Toplevel(self.root)
                tip_window.title("Troubleshooting Tips")
                tip_window.geometry("600x300")
                
                frame = ttk.Frame(tip_window, padding=20)
                frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(frame, text="Troubleshooting Tips:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
                
                tips_text = scrolledtext.ScrolledText(frame, height=10, font=('Arial', 10))
                tips_text.pack(fill=tk.BOTH, expand=True, pady=5)
                tips_text.insert('1.0', '\n'.join(tips))
                tips_text.config(state='disabled')
                
                ttk.Button(frame, text="Close", command=tip_window.destroy).pack(pady=5)
        finally:
            self.root.config(cursor="")
    
    def display_results(self):
        """Display backtest results in all tabs"""
        self.display_summary()
        self.display_equity_curve()
        self.display_trade_analysis()
        self.display_time_analysis()
        self.display_distribution_analysis()
        self.display_trade_details()
    
    def display_summary(self):
        """Display summary metrics"""
        # Clear existing widgets
        for widget in self.summary_tab.winfo_children():
            widget.destroy()
        
        # Create scrollable frame
        canvas = tk.Canvas(self.summary_tab)
        scrollbar = ttk.Scrollbar(self.summary_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display metrics in a nice grid
        metrics = self.backtest_engine.metrics
        
        row = 0
        for category, items in [
            ("Trade Summary", ['Total Trades', 'Winning Trades', 'Losing Trades', 'Win Rate (%)']),
            ("Returns", ['Total P&L ($)', 'Total Return (%)', 'Final Capital ($)']),
            ("Win/Loss Statistics", ['Average Win ($)', 'Average Loss ($)', 'Largest Win ($)', 
                                     'Largest Loss ($)', 'Avg Win (%)', 'Avg Loss (%)']),
            ("Risk Metrics", ['Profit Factor', 'Max Drawdown (%)', 'Sharpe Ratio', 'Expectancy ($)']),
            ("Trade Characteristics", ['Avg Trade Duration (min)', 'Max Consecutive Wins', 
                                       'Max Consecutive Losses'])
        ]:
            # Category header
            ttk.Label(scrollable_frame, text=category, font=('Arial', 12, 'bold')).grid(
                row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 5))
            row += 1
            
            # Metrics
            for metric in items:
                if metric in metrics:
                    ttk.Label(scrollable_frame, text=metric + ":", font=('Arial', 10)).grid(
                        row=row, column=0, sticky=tk.W, padx=20, pady=2)
                    
                    value = metrics[metric]
                    color = 'green' if isinstance(value, (int, float)) and value > 0 else 'red' if isinstance(value, (int, float)) and value < 0 else 'black'
                    
                    label = ttk.Label(scrollable_frame, text=str(value), font=('Arial', 10, 'bold'))
                    label.grid(row=row, column=1, sticky=tk.W, padx=20, pady=2)
                    
                    row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def display_equity_curve(self):
        """Display equity curve chart"""
        # Clear existing widgets
        for widget in self.equity_tab.winfo_children():
            widget.destroy()
        
        # Create figure
        fig = Figure(figsize=(12, 8), dpi=100)
        
        # Equity curve
        ax1 = fig.add_subplot(2, 1, 1)
        equity_df = pd.DataFrame(self.backtest_engine.equity_curve)
        ax1.plot(equity_df['timestamp'], equity_df['equity'], linewidth=2, color='blue')
        ax1.axhline(y=self.initial_capital.get(), color='red', linestyle='--', label='Initial Capital')
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Equity ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        ax2 = fig.add_subplot(2, 1, 2)
        equity_series = equity_df['equity']
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max * 100
        ax2.fill_between(equity_df['timestamp'], drawdowns, 0, alpha=0.3, color='red')
        ax2.plot(equity_df['timestamp'], drawdowns, linewidth=1, color='red')
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.equity_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def display_trade_analysis(self):
        """Display trade analysis charts"""
        # Clear existing widgets
        for widget in self.trades_tab.winfo_children():
            widget.destroy()
        
        trades_df = self.backtest_engine.trades_df
        
        # Create figure
        fig = Figure(figsize=(14, 10), dpi=100)
        
        # 1. P&L per trade
        ax1 = fig.add_subplot(2, 2, 1)
        colors = ['green' if x > 0 else 'red' for x in trades_df['pnl']]
        ax1.bar(range(len(trades_df)), trades_df['pnl'], color=colors, alpha=0.6)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.set_title('P&L per Trade', fontweight='bold')
        ax1.set_xlabel('Trade Number')
        ax1.set_ylabel('P&L ($)')
        ax1.grid(True, alpha=0.3)
        
        # 2. Cumulative P&L
        ax2 = fig.add_subplot(2, 2, 2)
        cumulative_pnl = trades_df['pnl'].cumsum()
        ax2.plot(cumulative_pnl, linewidth=2, color='blue')
        ax2.fill_between(range(len(cumulative_pnl)), cumulative_pnl, alpha=0.3)
        ax2.set_title('Cumulative P&L', fontweight='bold')
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('Cumulative P&L ($)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Win/Loss distribution
        ax3 = fig.add_subplot(2, 2, 3)
        wins = trades_df[trades_df['pnl'] > 0]['pnl']
        losses = trades_df[trades_df['pnl'] <= 0]['pnl']
        ax3.hist([wins, losses], bins=20, label=['Wins', 'Losses'], color=['green', 'red'], alpha=0.6)
        ax3.set_title('Win/Loss Distribution', fontweight='bold')
        ax3.set_xlabel('P&L ($)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Trade duration vs P&L
        ax4 = fig.add_subplot(2, 2, 4)
        colors = ['green' if x > 0 else 'red' for x in trades_df['pnl']]
        ax4.scatter(trades_df['duration'], trades_df['pnl'], c=colors, alpha=0.6, s=50)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_title('Trade Duration vs P&L', fontweight='bold')
        ax4.set_xlabel('Duration (minutes)')
        ax4.set_ylabel('P&L ($)')
        ax4.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.trades_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def display_time_analysis(self):
        """Display time-based analysis"""
        # Clear existing widgets
        for widget in self.time_tab.winfo_children():
            widget.destroy()
        
        trades_df = self.backtest_engine.trades_df
        
        # Create figure
        fig = Figure(figsize=(14, 10), dpi=100)
        
        # 1. P&L by Hour of Day
        ax1 = fig.add_subplot(2, 2, 1)
        hourly_pnl = trades_df.groupby('entry_hour')['pnl'].sum()
        colors = ['green' if x > 0 else 'red' for x in hourly_pnl]
        ax1.bar(hourly_pnl.index, hourly_pnl.values, color=colors, alpha=0.6)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.set_title('P&L by Hour of Day', fontweight='bold')
        ax1.set_xlabel('Hour')
        ax1.set_ylabel('Total P&L ($)')
        ax1.grid(True, alpha=0.3)
        
        # 2. Win Rate by Hour
        ax2 = fig.add_subplot(2, 2, 2)
        hourly_winrate = trades_df.groupby('entry_hour').apply(
            lambda x: (x['pnl'] > 0).sum() / len(x) * 100
        )
        ax2.plot(hourly_winrate.index, hourly_winrate.values, marker='o', linewidth=2, color='blue')
        ax2.set_title('Win Rate by Hour', fontweight='bold')
        ax2.set_xlabel('Hour')
        ax2.set_ylabel('Win Rate (%)')
        ax2.grid(True, alpha=0.3)
        
        # 3. P&L by Day of Week
        ax3 = fig.add_subplot(2, 2, 3)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_pnl = trades_df.groupby('entry_day')['pnl'].sum()
        daily_pnl = daily_pnl.reindex([d for d in day_order if d in daily_pnl.index])
        colors = ['green' if x > 0 else 'red' for x in daily_pnl]
        ax3.bar(range(len(daily_pnl)), daily_pnl.values, color=colors, alpha=0.6)
        ax3.set_xticks(range(len(daily_pnl)))
        ax3.set_xticklabels(daily_pnl.index, rotation=45)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.set_title('P&L by Day of Week', fontweight='bold')
        ax3.set_ylabel('Total P&L ($)')
        ax3.grid(True, alpha=0.3)
        
        # 4. Number of Trades by Hour
        ax4 = fig.add_subplot(2, 2, 4)
        trades_per_hour = trades_df['entry_hour'].value_counts().sort_index()
        ax4.bar(trades_per_hour.index, trades_per_hour.values, color='steelblue', alpha=0.6)
        ax4.set_title('Trade Frequency by Hour', fontweight='bold')
        ax4.set_xlabel('Hour')
        ax4.set_ylabel('Number of Trades')
        ax4.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.time_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def display_distribution_analysis(self):
        """Display statistical distribution analysis"""
        # Clear existing widgets
        for widget in self.dist_tab.winfo_children():
            widget.destroy()
        
        trades_df = self.backtest_engine.trades_df
        
        # Create figure
        fig = Figure(figsize=(14, 10), dpi=100)
        
        # 1. P&L Distribution
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.hist(trades_df['pnl'], bins=30, color='steelblue', alpha=0.6, edgecolor='black')
        ax1.axvline(x=trades_df['pnl'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: ${trades_df["pnl"].mean():.2f}')
        ax1.axvline(x=trades_df['pnl'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: ${trades_df["pnl"].median():.2f}')
        ax1.set_title('P&L Distribution', fontweight='bold')
        ax1.set_xlabel('P&L ($)')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Returns Distribution (%)
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.hist(trades_df['pnl_pct'], bins=30, color='orange', alpha=0.6, edgecolor='black')
        ax2.axvline(x=trades_df['pnl_pct'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {trades_df["pnl_pct"].mean():.2f}%')
        ax2.set_title('Returns Distribution (%)', fontweight='bold')
        ax2.set_xlabel('Return (%)')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Trade Duration Distribution
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.hist(trades_df['duration'], bins=30, color='purple', alpha=0.6, edgecolor='black')
        ax3.axvline(x=trades_df['duration'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {trades_df["duration"].mean():.2f} min')
        ax3.set_title('Trade Duration Distribution', fontweight='bold')
        ax3.set_xlabel('Duration (minutes)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Q-Q Plot
        ax4 = fig.add_subplot(2, 2, 4)
        from scipy import stats
        stats.probplot(trades_df['pnl'], dist="norm", plot=ax4)
        ax4.set_title('Q-Q Plot (Normality Test)', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.dist_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def display_trade_details(self):
        """Display detailed trade table"""
        # Clear existing widgets
        for widget in self.detail_tab.winfo_children():
            widget.destroy()
        
        # Create treeview
        tree_frame = ttk.Frame(self.detail_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ['Trade #', 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 
                   'Shares', 'P&L ($)', 'P&L (%)', 'Duration (min)']
        
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)
        
        # Insert data
        trades_df = self.backtest_engine.trades_df
        for idx, trade in trades_df.iterrows():
            values = (
                idx + 1,
                trade['entry_time'].strftime('%Y-%m-%d %H:%M'),
                trade['exit_time'].strftime('%Y-%m-%d %H:%M'),
                f"${trade['entry_price']:.2f}",
                f"${trade['exit_price']:.2f}",
                f"{trade['shares']:.2f}",
                f"${trade['pnl']:.2f}",
                f"{trade['pnl_pct']:.2f}%",
                f"{trade['duration']:.0f}"
            )
            
            # Color code based on P&L
            tag = 'profit' if trade['pnl'] > 0 else 'loss'
            tree.insert('', 'end', values=values, tags=(tag,))
        
        # Tag configuration
        tree.tag_configure('profit', background='#90EE90')
        tree.tag_configure('loss', background='#FFB6C6')
        
        # Pack
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Export button
        export_frame = ttk.Frame(self.detail_tab)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Export to CSV", 
                  command=self.export_trades).pack(side=tk.LEFT, padx=5)
    
    def export_trades(self):
        """Export trades to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.backtest_engine.trades_df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Trades exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def show_quick_reference(self):
        """Show quick reference guide"""
        ref_window = tk.Toplevel(self.root)
        ref_window.title("Quick Reference")
        ref_window.geometry("700x500")
        
        frame = ttk.Frame(ref_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        text = scrolledtext.ScrolledText(frame, font=('Courier', 9), wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        reference = """
QUICK REFERENCE GUIDE
=====================

STRATEGY STRUCTURE
------------------
Your strategy code should follow this pattern:

1. Calculate indicators
   df['SMA_20'] = df['close'].rolling(window=20).mean()

2. Initialize variables
   signals = []
   position = 0

3. Loop through data
   for i in range(start_index, len(df)):
       timestamp = df.index[i]  # Timestamp from index
       price = df['close'].iloc[i]
       
       # Your buy/sell logic
       if buy_condition and position == 0:
           signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
           position = 1
       
       elif sell_condition and position == 1:
           signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
           position = 0

AVAILABLE DATA COLUMNS
----------------------
- df.index → timestamps (datetime)
- df['open'] → opening price
- df['high'] → high price  
- df['low'] → low price
- df['close'] → closing price
- df['volume'] → trading volume
- df['vwap'] → volume-weighted average price (if available)

SIGNAL FORMAT
-------------
Each signal must be a dictionary:
{
    'timestamp': <pandas.Timestamp>,
    'type': 'BUY' or 'SELL',
    'price': <float>
}

COMMON INDICATORS
-----------------
# Simple Moving Average
df['SMA'] = df['close'].rolling(window=20).mean()

# Exponential Moving Average  
df['EMA'] = df['close'].ewm(span=12).mean()

# RSI
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# Bollinger Bands
df['BB_Middle'] = df['close'].rolling(20).mean()
df['BB_Std'] = df['close'].rolling(20).std()
df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)

TROUBLESHOOTING
---------------
Error: KeyError 'timestamp'
→ Check CSV has 'timestamp' column
→ Use 'Preview Data' button to verify

Error: No signals generated
→ Verify buy/sell conditions
→ Check loop range starts after indicator period
→ Print signals list to debug

Error: IndexError
→ Start loop after indicator calculation period
→ Example: for i in range(50, len(df))

TIPS
----
✓ Start loop after longest indicator period
✓ Use iloc[i] for integer indexing
✓ Track position: 0 = no position, 1 = long
✓ Always append to signals list
✓ Test with sample data first
"""
        
        text.insert('1.0', reference)
        text.config(state='disabled')
        
        ttk.Button(frame, text="Close", command=ref_window.destroy).pack(pady=5)
    
    def show_examples(self):
        """Show example strategies"""
        ex_window = tk.Toplevel(self.root)
        ex_window.title("Example Strategies")
        ex_window.geometry("800x600")
        
        frame = ttk.Frame(ex_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Click on a strategy to copy to clipboard:", 
                 font=('Arial', 11, 'bold')).pack(pady=5)
        
        # Create notebook for different strategies
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        strategies = {
            "RSI Mean Reversion": """# RSI Mean Reversion Strategy
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

signals = []
position = 0

for i in range(20, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    rsi = df['RSI'].iloc[i]
    
    if rsi < 30 and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    elif rsi > 70 and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0""",
            
            "Bollinger Bands": """# Bollinger Bands Breakout
df['SMA_20'] = df['close'].rolling(20).mean()
df['STD_20'] = df['close'].rolling(20).std()
df['Upper_BB'] = df['SMA_20'] + (df['STD_20'] * 2)
df['Lower_BB'] = df['SMA_20'] - (df['STD_20'] * 2)

signals = []
position = 0

for i in range(20, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    upper = df['Upper_BB'].iloc[i]
    lower = df['Lower_BB'].iloc[i]
    
    if price <= lower and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    elif price >= upper and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0""",
            
            "VWAP": """# VWAP Mean Reversion
signals = []
position = 0

for i in range(10, len(df)):
    timestamp = df.index[i]
    price = df['close'].iloc[i]
    vwap = df['vwap'].iloc[i]
    
    deviation = ((price - vwap) / vwap) * 100
    
    if deviation < -1.0 and position == 0:
        signals.append({'timestamp': timestamp, 'type': 'BUY', 'price': price})
        position = 1
    elif deviation > 1.0 and position == 1:
        signals.append({'timestamp': timestamp, 'type': 'SELL', 'price': price})
        position = 0"""
        }
        
        for name, code in strategies.items():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=name)
            
            text = scrolledtext.ScrolledText(tab, font=('Courier', 9))
            text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text.insert('1.0', code)
            text.config(state='disabled')
            
            def copy_code(c=code):
                self.root.clipboard_clear()
                self.root.clipboard_append(c)
                messagebox.showinfo("Copied", "Strategy copied to clipboard!")
            
            ttk.Button(tab, text="Copy to Clipboard", 
                      command=copy_code).pack(pady=5)
        
        ttk.Button(frame, text="Close", command=ex_window.destroy).pack(pady=5)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
Advanced Backtesting Dashboard
Version 1.0

A comprehensive GUI application for backtesting 
Python-based trading strategies on 1-minute stock data.

Features:
• Real-time strategy execution
• 15+ performance metrics
• 10+ visualization types
• Time-based analysis
• Statistical distributions
• Export capabilities

Built with Python, tkinter, pandas, matplotlib
        """
        messagebox.showinfo("About", about_text.strip())


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    style.theme_use('clam')
    
    app = BacktestingDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
