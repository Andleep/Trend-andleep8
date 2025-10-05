import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="بوت تداول", layout="wide")
st.title("💰 بوت التداول البسيط")

if 'balance' not in st.session_state:
    st.session_state.balance = 1000.0
    st.session_state.trades = []

if st.button("🔄 إجراء صفقة"):
    profit = random.uniform(-20, 30)
    st.session_state.balance += profit
    st.session_state.trades.append({
        'time': datetime.now(),
        'profit': profit,
        'balance': st.session_state.balance
    })
    
    st.success(f"تمت الصفقة! الربح: ${profit:.2f}")

st.metric("الرصيد", f"${st.session_state.balance:.2f}")
st.metric("عدد الصفقات", len(st.session_state.trades))

if st.session_state.trades:
    st.subheader("آخر الصفقات")
    for trade in st.session_state.trades[-5:]:
        st.write(f"{trade['time'].strftime('%H:%M')} - الربح: ${trade['profit']:.2f}")
