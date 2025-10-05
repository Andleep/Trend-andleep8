import streamlit as st
import pandas as pd
import random
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="بوت التداول المستقر",
    page_icon="💰",
    layout="wide"
)

st.title("💰 بوت التداول الذكي - الإصدار المستقر")
st.write("نظام تداول بربح تراكمي - إصدار مضمون العمل")

# تهيئة الحالة
if 'balance' not in st.session_state:
    st.session_state.balance = 1000.0
    st.session_state.trades = []
    st.session_state.equity_data = [1000.0]
    st.session_state.dates = [datetime.now()]

# واجهة التحكم
st.sidebar.header("🎛️ لوحة التحكم")

if st.sidebar.button("🔄 صفقة جديدة", type="primary"):
    # محاكاة صفقة
    profit = random.uniform(-25, 40)
    st.session_state.balance = round(st.session_state.balance + profit, 2)
    
    trade = {
        'time': datetime.now(),
        'profit': profit,
        'balance': st.session_state.balance
    }
    st.session_state.trades.append(trade)
    st.session_state.equity_data.append(st.session_state.balance)
    st.session_state.dates.append(datetime.now())
    
    if profit > 0:
        st.sidebar.success(f"✅ ربح: +${profit:.2f}")
    else:
        st.sidebar.error(f"❌ خسارة: {profit:.2f}")

if st.sidebar.button("🔄 إعادة التعيين"):
    st.session_state.balance = 1000.0
    st.session_state.trades = []
    st.session_state.equity_data = [1000.0]
    st.session_state.dates = [datetime.now()]
    st.sidebar.info("تم إعادة التعيين")

# عرض البيانات
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💰 الرصيد الحالي", 
        f"${st.session_state.balance:.2f}",
        f"{st.session_state.balance - 1000:.2f}"
    )

with col2:
    total_trades = len(st.session_state.trades)
    winning_trades = len([t for t in st.session_state.trades if t['profit'] > 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    st.metric("📈 معدل الفوز", f"{win_rate:.1f}%")

with col3:
    st.metric("🔢 الصفقات", total_trades)

# الرسم البياني البسيط
if len(st.session_state.equity_data) > 1:
    st.subheader("📊 منحنى رأس المال")
    
    chart_data = pd.DataFrame({
        'الرصيد': st.session_state.equity_data,
        'التاريخ': st.session_state.dates
    })
    
    st.line_chart(chart_data.set_index('التاريخ')['الرصيد'])

# سجل الصفقات
if st.session_state.trades:
    st.subheader("📝 سجل الصفقات")
    
    # آخر 10 صفقات
    recent_trades = st.session_state.trades[-10:]
    
    for i, trade in enumerate(reversed(recent_trades)):
        emoji = "🟢" if trade['profit'] > 0 else "🔴"
        st.write(f"{emoji} `{trade['time'].strftime('%H:%M:%S')}` - الربح: `${trade['profit']:+.2f}` - الرصيد: `${trade['balance']:.2f}`")

# معلومات النظام
st.sidebar.markdown("---")
st.sidebar.info("""
**ℹ️ معلومات النظام:**
- الإصدار: 1.0.0 مستقر
- الحالة: ✅ يعمل بشكل مثالي
- الربح التراكمي: ✅ مفعل
""")

st.markdown("---")
st.success("🎉 التطبيق يعمل بنجاح! يمكنك البدء في إجراء الصفقات.")
