import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
import time

# Sahifa sozlamalari
st.set_page_config(page_title="Order Flow Dashboard", layout="wide")

# 1. Sidebar sozlamalari
st.sidebar.header("Sozlamalar")
symbol = st.sidebar.text_input("Aktiv (Binance):", value="BTC/USDT")
min_volume = st.sidebar.number_input("Minimal lot hajmi ($):", value=5000)

# 2. Birja ulanishi (keshda saqlaymiz)
@st.cache_resource
def get_exchange():
    return ccxt.binance()

exchange = get_exchange()

# 3. Ma'lumotlarni olish funksiyasi
def fetch_market_data():
    try:
        # Shamlar
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['time', 'Open', 'High', 'Low', 'Close', 'Vol'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        # Stakan
        ob = exchange.fetch_order_book(symbol, limit=20)
        bid_vol = sum([b[1] for b in ob['bids']])
        ask_vol = sum([a[1] for a in ob['asks']])
        imbalance = (bid_vol / (bid_vol + ask_vol)) * 100

        # Bitimlar (Lenta)
        trades = exchange.fetch_trades(symbol, limit=20)
        
        return df, imbalance, trades
    except Exception as e:
        st.error(f"Ma'lumot olishda xato: {e}")
        return None, None, None

# 4. Dashboard interfeysi
st.title(f"🚀 {symbol} Real-Time Flow")
col1, col2, col3 = st.columns([2, 1, 1])

df, imbalance, trades = fetch_market_data()

if df is not None:
    with col1:
        fig = go.Figure(data=[go.Candlestick(
            x=df['time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
        )])
        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Stakan Balansi")
        st.metric("Oluvchilar", f"{imbalance:.1f}%")
        st.progress(imbalance / 100)
        st.metric("Sotuvchilar", f"{100-imbalance:.1f}%")

    with col3:
        st.subheader("Katta bitimlar")
        for t in trades:
            cost = t['price'] * t['amount']
            if cost >= min_volume:
                color = "green" if t['side'] == 'buy' else "red"
                st.markdown(f":{color}[{t['side'].upper()} | ${cost:,.0f} | {t['datetime'][11:19]}]")

# 5. Avtomatik yangilash (Har 2 soniyada)
time.sleep(2)
st.rerun()