import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
import time

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Order Flow Dashboard", layout="wide", initial_sidebar_state="expanded")

# 2. Sidebar - Sozlamalar menyusi
st.sidebar.header("📊 Sozlamalar")
# Bybit birjasida aktivlar odatda 'BTCUSDT' formatida bo'ladi
symbol = st.sidebar.text_input("Aktiv (Bybit formatida):", value="BTCUSDT")
min_volume = st.sidebar.number_input("Minimal lot hajmi ($):", value=5000, step=1000)
timeframe = st.sidebar.selectbox("Vaqt oralig'i (Grafik):", ['1m', '5m', '15m', '1h'], index=0)

# 3. Birja ulanishi (Bybit geografik cheklovlarda ancha yumshoq)
@st.cache_resource
def get_exchange():
    # Bybit global serverlaridan foydalanamiz
    return ccxt.bybit({'enableRateLimit': True})

exchange = get_exchange()

# 4. Ma'lumotlarni olish funksiyasi
def fetch_data(symbol):
    try:
        # Shamlar (Grafik uchun)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
        df = pd.DataFrame(ohlcv, columns=['time', 'Open', 'High', 'Low', 'Close', 'Vol'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        # Stakan (Order Book)
        ob = exchange.fetch_order_book(symbol, limit=50)
        bid_vol = sum([b[1] for b in ob['bids']])
        ask_vol = sum([a[1] for a in ob['asks']])
        imbalance = (bid_vol / (bid_vol + ask_vol)) * 100

        # Lenta (Recent Trades)
        trades = exchange.fetch_trades(symbol, limit=30)
        
        return df, imbalance, trades
    except Exception as e:
        st.error(f"Ma'lumot olishda xato: {e}")
        return None, None, None

# 5. Dashboard Interfeysi (UI)
st.title(f"🚀 {symbol} Real-Vaqt Tahlili")
st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 1])

df, imbalance, trades = fetch_data(symbol)

if df is not None:
    # --- 1-Ustun: Grafik ---
    with col1:
        st.subheader("Narx Grafigi")
        fig = go.Figure(data=[go.Candlestick(
            x=df['time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.update_layout(
            template="plotly_dark", 
            height=500, 
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- 2-Ustun: Order Book Imbalance ---
    with col2:
        st.subheader("Stakan Balansi")
        st.metric("Xaridorlar (Bids)", f"{imbalance:.1f}%")
        st.progress(imbalance / 100)
        st.metric("Sotuvchilar (Asks)", f"{100-imbalance:.1f}%")
        
        # Vizual ko'rsatkich
        if imbalance > 60:
            st.success("🔥 Kuchli Xarid Bosimi")
        elif imbalance < 40:
            st.error("📉 Kuchli Sotuv Bosimi")
        else:
            st.info("⚖️ Bozor Muvozanatda")

    # --- 3-Ustun: Katta Bitimlar (Lenta) ---
    with col3:
        st.subheader("Yirik Bitimlar")
        for t in trades:
            cost = float(t['price']) * float(t['amount'])
            if cost >= min_volume:
                color = "green" if t['side'] == 'buy' else "red"
                icon = "🟢" if t['side'] == 'buy' else "🔴"
                # Vaqtni formatlash
                trade_time = t['datetime'][11:19]
                st.markdown(f"{icon} **{t['side'].upper()}** | ${cost:,.0f} | {trade_time}")

# 6. Avtomatik yangilash
time.sleep(2)
st.rerun()
