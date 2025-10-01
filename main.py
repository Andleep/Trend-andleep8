# main.py (no pandas version)
import os, time, threading, csv
from datetime import datetime
from flask import Flask, jsonify, send_file
import requests

# config from env
SYMBOLS = os.getenv("SYMBOLS", "ETHUSDT,BTCUSDT,BNBUSDT,SOLUSDT,ADAUSDT").split(",")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
EMA_SHORT = int(os.getenv("EMA_SHORT", "20"))
EMA_LONG = int(os.getenv("EMA_LONG", "50"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.2"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.01"))
TRADE_LOG = os.getenv("TRADE_LOG", "trades.csv")
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "10.0"))
KL_LIMIT = int(os.getenv("KL_LIMIT", "200"))

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

app = Flask(__name__)

# state
balance_lock = threading.Lock()
balance = INITIAL_BALANCE
current_trade = None
trades = []
stats = {"trades":0, "wins":0, "losses":0, "profit_usd":0.0}

# helpers to fetch klines
def fetch_klines_raw(symbol, interval="1m", limit=KL_LIMIT):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(BINANCE_KLINES, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    # data: list of lists; we extract close and volume columns
    closes = [float(item[4]) for item in data]
    volumes = [float(item[5]) for item in data]
    return closes, volumes

# simple EMA implementation (list based)
def ema_list(values, span):
    if not values:
        return []
    alpha = 2.0 / (span + 1)
    emas = [values[0]]
    for v in values[1:]:
        emas.append((v - emas[-1]) * alpha + emas[-1])
    return emas

# simple RSI implementation (list based)
def compute_rsi_list(values, period=14):
    if len(values) < period+1:
        return [50]*len(values)
    deltas = [values[i] - values[i-1] for i in range(1, len(values))]
    seed_up = sum(x for x in deltas[:period] if x>0)
    seed_down = -sum(x for x in deltas[:period] if x<0)
    up = seed_up / period
    down = seed_down / period
    rsis = [50]*(period+1)
    for d in deltas[period:]:
        up = (up*(period-1) + (d if d>0 else 0)) / period
        down = (down*(period-1) + (-d if d<0 else 0)) / period
        rs = up / (down + 1e-12)
        rsi = 100 - (100/(1+rs))
        rsis.append(rsi)
    return rsis if rsis else [50]

# logging trades
def append_trade_csv(tr):
    header = ["time","symbol","side","entry","exit","profit_usd","balance_after","reason"]
    exists = False
    try:
        open(TRADE_LOG, "r").close()
        exists = True
    except Exception:
        exists = False
    with open(TRADE_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow([tr["time"], tr["symbol"], tr["side"], f"{tr['entry']:.8f}",
                         f"{tr['exit']:.8f}", f"{tr['profit']:.8f}", f"{tr['balance_after']:.8f}", tr["reason"]])

def enter_trade(symbol, entry_price):
    global current_trade, balance
    if current_trade is not None:
        return False
    qty = balance / entry_price
    stop_price = entry_price * (1 - STOP_LOSS_PCT)
    current_trade = {"symbol":symbol, "entry_price":entry_price, "qty":qty, "stop_price":stop_price, "entry_time":datetime.utcnow().isoformat(), "side":"LONG"}
    print(f"[ENTER] {symbol} @ {entry_price:.6f} qty={qty:.8f} bal={balance:.8f}")
    return True

def exit_trade(exit_price, reason="X"):
    global current_trade, balance, stats, trades
    if current_trade is None:
        return False
    proceeds = current_trade["qty"] * exit_price
    cost = current_trade["qty"] * current_trade["entry_price"]
    profit = proceeds - cost
    balance = proceeds
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
    print(f"[EXIT] {tr['symbol']} exit {exit_price:.6f} profit={profit:.8f} newbal={balance:.8f} reason={reason}")
    current_trade = None
    return True

def evaluate_symbol(sym):
    global current_trade
    try:
        closes, volumes = fetch_klines_raw(sym)
    except Exception as e:
        print("fetch error", sym, e)
        return None, None
    if len(closes) < max(EMA_LONG, RSI_PERIOD) + 5:
        return None, None
    ema_s = ema_list(closes, EMA_SHORT)
    ema_l = ema_list(closes, EMA_LONG)
    # RSI list aligned to closes length
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
    # volume filter
    avg_vol = sum(volumes[-(20+2):-2]) / 20.0 if len(volumes) >= 22 else sum(volumes[:-1])/(len(volumes)-1)
    vol_ok = volumes[last_idx] > (avg_vol * VOLUME_MULTIPLIER)
    rsi_now = rsi_list[-1] if len(rsi_list)>0 else 50
    rsi_ok = (rsi_now > 25) and (rsi_now < 75)
    if current_trade is None:
        if cross_up and vol_ok and rsi_ok:
            return "enter", float(last_close)
        else:
            return None, None
    else:
        if current_trade["symbol"] == sym:
            if last_close <= current_trade["stop_price"]:
                return "exit_sl", float(last_close)
            if cross_down:
                return "exit_x", float(last_close)
    return None, None

def worker_loop():
    global current_trade
    print("Worker started. Symbols:", SYMBOLS)
    while True:
        try:
            for s in SYMBOLS:
                decision, price = evaluate_symbol(s)
                if decision == "enter":
                    if current_trade is None:
                        enter_trade(s, price)
                elif decision == "exit_sl":
                    exit_trade(price, reason="SL")
                elif decision == "exit_x":
                    exit_trade(price, reason="X")
        except Exception as e:
            print("Worker error:", e)
        time.sleep(POLL_SECONDS)

@app.route("/status")
def status():
    bal = balance
    ct = current_trade.copy() if current_trade else None
    s = dict(stats)
    recent = list(reversed(trades[-20:]))
    return jsonify({"balance": round(bal,8), "current_trade": ct, "stats": s, "recent_trades": recent})

@app.route("/download_trades")
def download_trades():
    try:
        return send_file(TRADE_LOG, as_attachment=True)
    except Exception:
        return jsonify({"error":"no trades yet"}), 404

def start_background():
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

if __name__ == "__main__":
    start_background()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8000")))
else:
    start_background()
