// static/app.js
const base = "/";
const symbolSelect = document.getElementById("symbolSelect");
const limitSelect = document.getElementById("limitSelect");
const refreshBtn = document.getElementById("refreshBtn");
const balanceEl = document.getElementById("balance");
const statsDiv = document.getElementById("stats");
const tradesTbody = document.querySelector("#tradesTable tbody");
const downloadLink = document.getElementById("download");

let chart;

async function api(path) {
  const res = await fetch('/api' + path);
  return res.json();
}

async function loadStatus() {
  const s = await api('/status');
  balanceEl.innerText = `الرصيد: $${(s.balance||0).toFixed(6)}`;
  // fill symbols
  const syms = s.symbols || [];
  symbolSelect.innerHTML = syms.map(x=>`<option value="${x}">${x}</option>`).join('');
  updateStatsUI(s);
  updateTradesUI(s.trades || []);
  await loadCandles();
}

function updateStatsUI(s) {
  statsDiv.innerHTML = `
    إجمالي الصفقات: ${s.stats.trades || 0} — فوز: <span class="green">${s.stats.wins||0}</span> — خسارة: <span class="red">${s.stats.losses||0}</span> — ربح $: ${(s.stats.profit_usd||0).toFixed(6)}
  `;
}

function updateTradesUI(trades) {
  tradesTbody.innerHTML = trades.slice().reverse().map(t=>`
    <tr>
      <td>${t.time}</td>
      <td>${t.symbol}</td>
      <td>${t.entry.toFixed(6)}</td>
      <td>${t.exit.toFixed(6)}</td>
      <td class="${t.profit>=0?'green':'red'}">${t.profit.toFixed(6)}</td>
      <td>${t.balance_after.toFixed(6)}</td>
      <td>${t.reason}</td>
    </tr>
  `).join('');
  downloadLink.href = '/download_trades';
}

async function loadCandles() {
  const symbol = symbolSelect.value || symbolSelect.options[0].value;
  const limit = limitSelect.value || 200;
  const data = await fetch(`/api/candles?symbol=${symbol}&limit=${limit}`).then(r=>r.json());
  if (data.error) {
    console.error(data);
    return;
  }
  buildChart(data.candles);
}

function buildChart(candles) {
  // format for chartjs financial
  const ds = candles.map(c=>({
    x: new Date(c.time),
    o: c.open,
    h: c.high,
    l: c.low,
    c: c.close
  }));
  const ctx = document.getElementById("chart").getContext("2d");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'candlestick',
    data: { datasets: [{ label: 'Price', data: ds }] },
    options: {
      plugins:{legend:{display:false}},
      scales:{x:{time:{unit:'minute'}}}
    }
  });
}

refreshBtn.onclick = ()=>{ loadStatus(); };

window.onload = ()=>{ loadStatus(); setInterval(loadStatus, 60*1000); };
