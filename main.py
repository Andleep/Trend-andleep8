# main.py (updated: robust Binance fetch + logging)
import os
import time
import threading
import csv
from datetime import datetime
from flask import Flask, jsonify, send_file, request, render_template
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------- CONFIG ----------
SYMBOLS = os.getenv("SYMBOLS", "ETHUSDT,BTCUSDT,BNBUSDT,SOLUSDT,ADAUSDT").split(",")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))   # polling interval (1m)
EMA_SHORT = int(os.getenv("EMA_SHORT", "20"))
EMA_LONG = int(os.getenv("EMA_LONG", "50"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.2"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.01"))  # 1%
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "10.0"))
KL_LIMIT = int(os.getenv("KL_LIMIT", "200"))
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

DEBUG_LOG = "bot_debug.log"
TRADE_LOG = "trades.csv"

# ---------- APP & STATE ----------
app = Flask(__name__, template_folder="templates", static_folder="static")
balance_lock = threading.Lock()
balance = INITIAL_BALANCE
current_trade = None   # dict: symbol, entry_price, qty, stop_price, entry_time
trades = []            # history of trades (in-memory)
stats = {"trades":0, "wins":0, "losses":0, "profit_usd": 0.0}

# ---------- Logging helper ----------
def debug_log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(line.strip())

# ---------- Requests session with retries ----------
def create_requests_session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

SESSION = create_requests_session()

# ---------- Network fetch with robust error messages ----------
def fetch_klines(symbol, interval="1m", limit=KL_LIMIT):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TradeBot/1.0; +https://example.com)",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        r = SESSION.get(BINANCE_KLINES, params=params, headers=headers, timeout=10)
        # Raise for HTTP errors (4xx/5xx)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            raise RuntimeError("unexpected response format from Binance")
        return data
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        text = e.response.text[:300] if e.response is not None else str(e)
        msg = f"Binance HTTP error {code}: {text}"
        debug_log(msg)
        raise RuntimeError(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Network/Request error: {str(e)}"
        debug_log(msg)
        raise RuntimeError(msg)
    except Exception as e:
        msg = f"Unexpected error fetching klines: {str(e)}"
        debug_log(msg)
        raise RuntimeError(msg)

# ---------- Small indicator implementations (list-based) ----------
def closes_volumes_from_klines(data):
    closes = [float(c[4]) for c in data]
    volumes = [float(c[5]) for c in data]
    times = [int(c[0]) for c in data]
    return closes, volumes, times

def ema_list(values, span):
    if not values:
        return []
    alpha = 2.0 / (span + 1)
    emas = [values[0]]
    for v in values[1:]:
        emas.append((v - emas[-1]) * alpha + emas[-1])
    return emas

def compute_rsi_list(values, period=14):
    if len(values) < period+1:
        return [50]*len(values)
    deltas = [values[i] - values[i-1] for i in range(1, len(values))]
    seed_up = sum(x for x in deltas[:period] if x>0)
    seed_down = -sum(x for x in deltas[:period] if x<0)
    up = seed_up / period if period>0 else 0
    down = seed_down / period if seed_down!=0 and period>0 else 1e-9
    rsis = [50]*(period+1)
    for d in deltas[period:]:
        up = (up*(period-1) + (d if d>0 else 0)) / period
        down = (down*(period-1) + (-d if d<0 else 0)) / period
        rs = up / (down + 1e-12)
        rsi = 100 - (100/(1+rs))
        rsis.append(rsi)
    return rsis if rsis else [50]

# ---------- Trade logging ----------
def append_trade_csv(tr):
    header = ["time","symbol","side","entry","exit","profit_usd","balance_after","reason"]
    try:
        exists = os.path.exists(TRADE_LOG)
    except Exception:
        exists = False
    try:
        with open(TRADE_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(header)
            writer.writerow([tr["time"], tr["symbol"], tr["side"], f"{tr['entry']:.8f}",
                             f"{tr['exit']:.8f}", f"{tr['profit']:.8f}", f"{tr['balance_after']:.8f}", tr["reason"]])
    except Exception as e:
        debug_log(f"Failed to write trade CSV: {e}")

# ---------- Trading simulation (entry/exit) ----------
def enter_trade(symbol, entry_price):
    global current_trade, balance
    with balance_lock:
        if current_trade is not None:
            return False
        qty = balance / entry_price
        stop_price = entry_price * (1 - STOP_LOSS_PCT)
        current_trade = {"symbol":symbol, "entry_price":entry_price, "qty":qty, "stop_price":stop_price, "entry_time":datetime.utcnow().isoformat(), "side":"LONG"}
        debug_log(f"ENTER {symbol} @ {entry_price:.6f} qty={qty:.8f} bal={balance:.8f}")
        return True

def exit_trade(exit_price, reason="X"):
    global current_trade, balance, trades, stats
    with balance_lock:
        if current_trade is None:
            return False
        proceeds = current_trade["qty"] * exit_price
        cost = current_trade["qty"] * current_trade["entry_price"]
        profit = proceeds - cost
        balance = proceeds  # compounding
        tr = {"time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
              "symbol": current_trade["symbol"], "side": current_trade["side"],
              "entry": current_trade["entry_price"], "exit": exit_price,
              "profit": profit, "balance_after": balance, "reason": reason}
        trades.append(tr)
        append_trade_csv(tr)
        stats["trades"] += 1
        if profit >= 0:
            stats["wins"] += 1
        else:
            stats["losses"] += 1
        stats["profit_usd"] = round(balance - INITIAL_BALANCE, 8)
        debug_log(f"EXIT {tr['symbol']} exit {exit_price:.6f} profit={profit:.8f} newbal={balance:.8f} reason={reason}")
        current_trade = None
        return True

# ---------- Decision logic ----------
def evaluate_symbol(symbol):
    global current_trade
    try:
        klines = fetch_klines(symbol)
    except Exception as e:
        debug_log(f"fetch error {symbol}: {e}")
        return None, None
    closes, volumes, times = closes_volumes_from_klines(klines)
    if len(closes) < max(EMA_LONG, RSI_PERIOD) + 5:
        return None, None
    ema_s = ema_list(closes, EMA_SHORT)
    ema_l = ema_list(closes, EMA_LONG)
    rsi_list = compute_rsi_list(closes, RSI_PERIOD)
    last_idx = -2
    prev_idx = -3
    s_now = ema_s[last_idx]
    s_prev = ema_s[prev_idx]
    l_now = ema_l[last_idx]
    l_prev = ema_l[prev_idx]
    cross_up = (s_prev <= l_prev) and (s_now > l_now)
    cross_down = (s_prev >= l_prev) and (s_now < l_now)
    last_close = closes[last_idx]
    if len(volumes) >= 22:
        avg_vol = sum(volumes[-(20+2):-2]) / 20.0
    else:
        avg_vol = sum(volumes[:-1])/(len(volumes)-1) if len(volumes)>1 else volumes[-1]
    vol_ok = volumes[last_idx] > (avg_vol * VOLUME_MULTIPLIER)
    rsi_now = rsi_list[-1] if len(rsi_list)>0 else 50
    rsi_ok = (rsi_now > 25) and (rsi_now < 75)
    if current_trade is None:
        if cross_up and vol_ok and rsi_ok:
            return "enter", float(last_close)
        else:
            return None, None
    else:
        if current_trade["symbol"] == symbol:
            if last_close <= current_trade["stop_price"]:
                return "exit_sl", float(last_close)
            if cross_down:
                return "exit_x", float(last_close)
    return None, None

# ---------- Worker ----------
def worker_loop():
    global current_trade
    debug_log("Worker started, symbols: " + ",".join(SYMBOLS))
    while True:
        try:
            for s in SYMBOLS:
                action, price = evaluate_symbol(s)
                if action == "enter":
                    with balance_lock:
                        if current_trade is None:
                            enter_trade(s, price)
                elif action == "exit_sl" or action == "exit_x":
                    exit_trade(price, reason="SL" if action=="exit_sl" else "X")
        except Exception as e:
            debug_log(f"Worker error: {e}")
        time.sleep(POLL_SECONDS)

def start_worker():
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

# ---------- Flask routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    with balance_lock:
        return jsonify({
            "balance": round(balance,8),
            "current_trade": current_trade,
            "stats": stats,
            "symbols": SYMBOLS,
            "trades": trades
        })

@app.route("/api/candles")
def api_candles():
    symbol = request.args.get("symbol", SYMBOLS[0])
    limit = int(request.args.get("limit", KL_LIMIT))
    try:
        klines = fetch_klines(symbol, limit=limit)
        out = []
        for k in klines:
            out.append({
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        return jsonify({"symbol": symbol, "candles": out})
    except Exception as e:
        debug_log(f"api/candles error for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/logs")
def api_logs():
    # return last 200 lines of debug log
    try:
        with open(DEBUG_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
        return "<pre>" + "".join(lines) + "</pre>"
    except Exception:
        return "<pre>(no logs yet)</pre>"

@app.route("/download_trades")
def download_trades():
    try:
        return send_file(TRADE_LOG, as_attachment=True)
    except Exception:
        return jsonify({"error":"no trades yet"}), 404

# start worker
start_worker()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8000")))
