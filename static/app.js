// static/app.js
const runBtn = document.getElementById("runBtn");
const symbolSelect = document.getElementById("symbolSelect");
const monthsSelect = document.getElementById("monthsSelect");
const statsDiv = document.getElementById("stats");
const tradesTbody = document.querySelector("#tradesTable tbody");
const balanceEl = document.getElementById("balance");
let chart;

async function runBacktest(){
  const symbol = symbolSelect.value;
  const months = monthsSelect.value;
  statsDiv.innerText = "جاري تشغيل المحاكاة...";
  try{
    const res = await fetch("/api/backtest", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({symbol: symbol, months: parseInt(months)})
    });
    const data = await res.json();
    if(data.error){
      statsDiv.innerText = "خطأ: " + data.error;
      return;
    }
    const stats = data.stats;
    const trades = data.trades;
    statsDiv.innerHTML = `البداية: $${stats.initial_balance} — النهاية: $${stats.final_balance} — صفقات: ${stats.trades} — فوز: ${stats.wins} — خسارة: ${stats.losses} — نسبة الفوز: ${stats.win_rate}%`;
    balanceEl.innerText = `الرصيد: $${stats.final_balance}`;
    updateTrades(trades);
    // draw candles if available (use first 500 candles via /api/candles)
    const candlesRes = await fetch(`/api/candles?symbol=${symbol}&limit=500`);
    const candlesJson = await candlesRes.json();
    if(!candlesJson.error){
      buildChart(candlesJson.candles);
    }
  }catch(e){
    statsDiv.innerText = "خطأ في التشغيل: " + e.toString();
  }
}

function updateTrades(trades){
  tradesTbody.innerHTML = trades.slice().reverse().map(t=>`<tr>
    <td>${new Date(t.time).toLocaleString()}</td>
    <td>${t.symbol||''}</td>
    <td>${t.entry?.toFixed(6)||''}</td>
    <td>${t.exit?.toFixed(6)||''}</td>
    <td class="${t.profit>=0?'green':'red'}">${t.profit?.toFixed(6)||''}</td>
    <td>${t.balance_after?.toFixed(6)||''}</td>
    <td>${t.reason||''}</td>
  </tr>`).join('');
}

function buildChart(candles){
  const ds = candles.map(c=>({x:new Date(c.time), o:c.open, h:c.high, l:c.low, c:c.close}));
  const ctx = document.getElementById("chart").getContext("2d");
  if(chart) chart.destroy();
  chart = new Chart(ctx, {
    type:'candlestick',
    data:{datasets:[{label:'Price', data:ds}]},
    options:{plugins:{legend:{display:false}}, scales:{x:{time:{unit:'minute'}}}}
  });
}

runBtn.onclick = runBacktest;
window.onload = ()=>{ };
