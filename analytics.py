import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np

# 1. Page Config
st.set_page_config(layout="wide", page_title="BTC Algo: RSI + MA")

# 2. Helper: Calculate RSI (Wilder's Smoothing)
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    # Use Exponential Moving Average with 'com' (Center of Mass) for Wilder's Smoothing
    # com = window - 1 is the standard convention for RSI
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 3. Load Data
@st.cache_data
def load_data():
    file_path = 'btc_hourly_history.csv'
    try:
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR CONTROLS ---
    st.sidebar.title("Strategy Parameters")
    
    st.sidebar.subheader("1. Trend (Moving Averages)")
    short_window = st.sidebar.slider("Fast MA", 5, 100, 20)
    long_window = st.sidebar.slider("Slow MA", 50, 365, 50)
    
    st.sidebar.subheader("2. Momentum (RSI Filter)")
    use_rsi = st.sidebar.checkbox("Enable RSI Filter", value=True)
    rsi_window = st.sidebar.slider("RSI Window", 5, 30, 14)
    rsi_overbought = st.sidebar.slider("Max RSI (Don't Buy if > X)", 50, 100, 70)
    
    st.sidebar.subheader("3. Backtest Settings")
    initial_capital = st.sidebar.number_input("Capital ($)", value=10000)
    
    # Date Filter
    min_date = df.index.min().date()
    max_date = df.index.max().date()
    start_date = st.sidebar.date_input("Start Date", min_date)
    end_date = st.sidebar.date_input("End Date", max_date)

    # --- CALCULATION ENGINE ---
    mask = (df.index.date >= start_date) & (df.index.date <= end_date)
    filtered_df = df.loc[mask].copy()

    # Calculate Indicators
    filtered_df['SMA_Short'] = filtered_df['CLOSE'].rolling(window=short_window).mean()
    filtered_df['SMA_Long'] = filtered_df['CLOSE'].rolling(window=long_window).mean()
    filtered_df['RSI'] = calculate_rsi(filtered_df['CLOSE'], window=rsi_window)

    # --- STRATEGY LOGIC ---
    # 1. Trend Condition: Fast MA > Slow MA
    trend_signal = filtered_df['SMA_Short'] > filtered_df['SMA_Long']
    
    # 2. RSI Condition: RSI < Overbought Level (Only buy if NOT overheated)
    if use_rsi:
        rsi_condition = filtered_df['RSI'] < rsi_overbought
        # Combine signals
        filtered_df['Signal'] = np.where(trend_signal & rsi_condition, 1, 0)
    else:
        filtered_df['Signal'] = np.where(trend_signal, 1, 0)

    # 3. Shift Signal to next candle to simulate real execution
    filtered_df['Position'] = filtered_df['Signal'].shift(1)
    
    # 4. Returns Calculation
    filtered_df['Market_Returns'] = filtered_df['CLOSE'].pct_change()
    filtered_df['Strategy_Returns'] = filtered_df['Market_Returns'] * filtered_df['Position']
    filtered_df['Cum_Strategy'] = (1 + filtered_df['Strategy_Returns']).cumprod() * initial_capital
    filtered_df['Cum_Market'] = (1 + filtered_df['Market_Returns']).cumprod() * initial_capital

    # Entries/Exits for plotting
    filtered_df['Trade_Signal'] = filtered_df['Signal'].diff()
    buys = filtered_df[filtered_df['Trade_Signal'] == 1]
    sells = filtered_df[filtered_df['Trade_Signal'] == -1]

    # --- VISUALIZATION (Subplots) ---
    st.title(f"Backtest: Trend + RSI Filter")

    # Create 2-row subplot (Price on top, RSI on bottom)
    fig = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # ROW 1: Price & MAs
    fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['CLOSE'], mode='lines', name='Price', line=dict(color='gray', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['SMA_Short'], mode='lines', name=f'SMA {short_window}', line=dict(color='#00ff00', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['SMA_Long'], mode='lines', name=f'SMA {long_window}', line=dict(color='#ff9900', width=1)), row=1, col=1)
    
    # Buy/Sell Markers
    fig.add_trace(go.Scatter(x=buys.index, y=buys['CLOSE'], mode='markers', name='Buy', marker=dict(symbol='triangle-up', size=10, color='#00ff00')), row=1, col=1)
    fig.add_trace(go.Scatter(x=sells.index, y=sells['CLOSE'], mode='markers', name='Sell', marker=dict(symbol='triangle-down', size=10, color='#ff0000')), row=1, col=1)

    # ROW 2: RSI
    fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['RSI'], name='RSI', line=dict(color='purple', width=1)), row=2, col=1)
    # Add Overbought/Oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Oversold")
    # Add the user's specific filter line
    if use_rsi:
        fig.add_hline(y=rsi_overbought, line_dash="dot", line_color="yellow", row=2, col=1, annotation_text="Filter Threshold")

    fig.update_layout(height=700, template="plotly_dark", hovermode="x unified", title="Strategy Visualization")
    st.plotly_chart(fig, use_container_width=True)

    # Metrics
    total_return = filtered_df['Cum_Strategy'].iloc[-1] - initial_capital
    market_return = filtered_df['Cum_Market'].iloc[-1] - initial_capital
    outperformance = total_return - market_return
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Strategy Profit", f"${total_return:,.2f}")
    c2.metric("Market Profit", f"${market_return:,.2f}")
    c3.metric("Net Edge", f"${outperformance:,.2f}", delta_color="normal" if outperformance > 0 else "inverse")

else:
    st.error("Data file not found.")