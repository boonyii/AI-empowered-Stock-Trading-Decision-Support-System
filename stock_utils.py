import yfinance as yf
import pandas as pd
import ta
import datetime


##########################################################################################
## PART 1: Define Functions for Pulling, Processing, and Creating Techincial Indicators ##
##########################################################################################



# Fetch stock data based on the ticker, period, and interval
def fetch_stock_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if data is None or data.empty:
            print(f"No data found for ticker {ticker}")
            return None
            
        return data
    except Exception as e:
        print(f"yfinance error for {ticker}: {e}")
        return None

# Process data to ensure it is timezone-aware and has the correct format
def process_data(data):
    if data is None or data.empty:
        return data
    
    # 1. Flatten MultiIndex columns immediately
    # This turns ('Close', 'AAPL') into just 'Close'
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # 2. Handle duplicate columns if they exist after flattening
    data = data.loc[:, ~data.columns.duplicated()].copy()

    # 3. Standard processing
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    
    # Ensure the date column is named 'Datetime' consistently
    if 'Date' in data.columns:
        data.rename(columns={'Date': 'Datetime'}, inplace=True)
            
    return data

# Calculate basic metrics from the stock data
def calculate_metrics(data):
    # Ensure we are looking at 1D values by using .iloc[-1]
    # We use .item() to convert a single-value Series to a standard Python float
    last_close = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2]
    
    # Force to float in case they are still single-value Series
    last_close = float(last_close.iloc[0]) if hasattr(last_close, 'iloc') else float(last_close)
    prev_close = float(prev_close.iloc[0]) if hasattr(prev_close, 'iloc') else float(prev_close)
    
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    
    high = data['High'].iloc[-1]
    low = data['Low'].iloc[-1]
    volume = data['Volume'].iloc[-1]
    last_open = data['Open'].iloc[-1]
    
    return last_close, change, pct_change, high, low, volume, last_open, last_close

def add_technical_indicators(data):
    # Ensure we are working with a 1D Series for technical analysis
    # If data['Close'] is a DataFrame (2 columns), .iloc[:, 0] picks the first one
    close_series = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
    
    data['SMA_20'] = ta.trend.sma_indicator(close_series, window=20)
    data['EMA_20'] = ta.trend.ema_indicator(close_series, window=20)
    data['RSI'] = ta.momentum.RSIIndicator(close_series, window=20).rsi()
    data["WMA_20"] = ta.trend.WMAIndicator(close_series, window=20).wma()
    data["KAMA"] = ta.momentum.KAMAIndicator(close_series).kama()
    return data