import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import random

# إعداد الصفحة
st.set_page_config(
    page_title="بوت التداول الذكي",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 بوت التداول الذكي - الإصدار النهائي")
st.markdown("نظام تداول بربح تراكمي فوري بعد كل صفقة")

# تهيئة الحالة
if 'balance' not in st.session_state:
    st.session_state.balance = 1000.0
    st.session_state.trades = []
    st.session_state.bot_running = False

# الشريط الجانبي
st.sidebar.header("الإعدادات")

# أزرار التحكم
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ بدء البوت", type="primary"):
        st.session_state.bot_running = True
        st.success("البوت يعمل الآن!")

with col2:
    if st.button("⏸️ إيقاف"):
        st.session_state.bot_running = False
        st.warning("البوت متوقف")

with col3:
    if st.button("🔄 صفقة تجريبية"):
        # محاكاة صفقة واقعية
        profit = random.uniform(-30, 50)
        st.session_state.balance += profit
        
        trade = {
            'time': datetime.now(),
            'profit': profit,
            'balance': st.session_state.balance,
            'type': 'BUY' if profit > 0 else 'SELL'
        }
        st.session_state.trades.append(trade)
        
        if profit > 0:
            st.success(f"✅ صفقة رابحة! +${profit:.2f}")
        else:
            st.error(f"❌ صفقة خاسرة! {profit:.2f}")

# عرض المعلومات
st.header("📊 لوحة التحكم")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("الرصيد الحالي", f"${st.session_state.balance:.2f}")

with col2:
    total_profit = st.session_state.balance - 1000
    st.metric("الربح الإجمالي", f"${total_profit:.2f}")

with col3:
    st.metric("عدد الصفقات", len(st.session_state.trades))

with col4:
    status = "🟢 يعمل" if st.session_state.bot_running else "🔴 متوقف"
    st.metric("حالة البوت", status)

# الرسم البياني
if st.session_state.trades:
    st.subheader("📈 تطور رأس المال")
    
    dates = [t['time'] for t in st.session_state.trades]
    balances = [t['balance'] for t in st.session_state.trades]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, 
        y=balances, 
        mode='lines+markers',
        name='رأس المال',
        line=dict(color='green', width=3)
    ))
    
    fig.update_layout(
        title="نمو رأس المال مع نظام الربح التراكمي",
        xaxis_title="الوقت",
        yaxis_title="رأس المال ($)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# سجل الصفقات
if st.session_state.trades:
    st.subheader("📝 آخر الصفقات")
    
    # عرض آخر 5 صفقات
    recent_trades = st.session_state.trades[-5:]
    for trade in reversed(recent_trades):
        emoji = "🟢" if trade['profit'] > 0 else "🔴"
        st.write(f"{emoji} {trade['time'].strftime('%H:%M:%S')} - الربح: ${trade['profit']:.2f} - الرصيد: ${trade['balance']:.2f}")

# نظام التشغيل التلقائي
if st.session_state.bot_running:
    st.info("🔄 البوت يعمل تلقائياً... (محاكاة)")

st.markdown("---")
st.success("✅ البوت جاهز للعمل! استخدم الأزرار أعلاه للتحكم.")
