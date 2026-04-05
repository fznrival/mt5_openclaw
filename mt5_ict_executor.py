import MetaTrader5 as mt5
import pandas as pd
import json
import os
from datetime import datetime
import requests

# =========================
# LOAD CONFIG
# =========================
with open("config.json", "r") as f:
    config = json.load(f)

SYMBOL = config["trading"]["symbol"]
LOT = config["trading"]["lot_size"]

TF_ENTRY = mt5.TIMEFRAME_M5
TF_HTF = mt5.TIMEFRAME_M15

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{config['telegram_bot_token']}/sendMessage"
        requests.post(url, data={
            "chat_id": config["telegram_chat_id"],
            "text": msg
        })
    except:
        pass

# =========================
# SESSION FILTER
# =========================
def get_active_session():
    now = datetime.now().strftime("%H:%M")
    for name, t in config["sessions"].items():
        if t[0] <= now <= t[1]:
            return name
    return None

# =========================
# MARKET DATA
# =========================
def get_data(tf, bars=100):
    rates = mt5.copy_rates_from_pos(SYMBOL, tf, 0, bars)
    return pd.DataFrame(rates)

# =========================
# HTF BIAS (SIMPLE STRUCTURE)
# =========================
def get_htf_bias(df):
    if df['close'].iloc[-1] > df['close'].iloc[-5]:
        return "bullish"
    else:
        return "bearish"

# =========================
# LIQUIDITY SWEEP
# =========================
def detect_sweep(df):
    if df['high'].iloc[-1] > df['high'].iloc[-2]:
        return "buy_sweep"
    if df['low'].iloc[-1] < df['low'].iloc[-2]:
        return "sell_sweep"
    return None

# =========================
# DISPLACEMENT (STRONG CANDLE)
# =========================
def detect_displacement(df):
    body = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    avg_body = (df['high'] - df['low']).rolling(10).mean().iloc[-1]

    if body > avg_body:
        return True
    return False

# =========================
# FVG VALID
# =========================
def detect_fvg(df):
    prev = df.iloc[-3]
    mid = df.iloc[-2]
    curr = df.iloc[-1]

    # Bullish FVG
    if prev['high'] < curr['low']:
        return "buy"

    # Bearish FVG
    if prev['low'] > curr['high']:
        return "sell"

    return None

# =========================
# ENTRY MODEL (ICT REAL FLOW)
# =========================
def get_trade_signal(df_entry, df_htf, session):
    bias = get_htf_bias(df_htf)
    sweep = detect_sweep(df_entry)
    displacement = detect_displacement(df_entry)
    fvg = detect_fvg(df_entry)

    if not sweep or not displacement or not fvg:
        return None

    # ALIGNMENT
    if bias == "bullish" and sweep == "sell_sweep" and fvg == "buy":
        return "buy"

    if bias == "bearish" and sweep == "buy_sweep" and fvg == "sell":
        return "sell"

    return None

# =========================
# RISK MANAGEMENT (STRUCTURE BASED)
# =========================
def calculate_sl_tp(signal, df):
    point = mt5.symbol_info(SYMBOL).point

    if signal == "buy":
        sl = df['low'].iloc[-3] - 5 * point
        tp = df['high'].iloc[-1] + 20 * point
    else:
        sl = df['high'].iloc[-3] + 5 * point
        tp = df['low'].iloc[-1] - 20 * point

    return sl, tp

# =========================
# EXECUTION
# =========================
def execute_trade(signal, sl, tp):
    tick = mt5.symbol_info_tick(SYMBOL)

    price = tick.ask if signal == "buy" else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": mt5.ORDER_TYPE_BUY if signal == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": config["trading"]["slippage_dev"],
        "magic": config["trading"]["magic_number"],
        "comment": "ICT_SCALP",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    return mt5.order_send(request)

# =========================
# POSITION FILTER
# =========================
def has_open_position():
    positions = mt5.positions_get(symbol=SYMBOL)
    return positions is not None and len(positions) > 0

# =========================
# MAIN
# =========================
def run():
    session = get_active_session()

    if not session:
        print("Outside killzone")
        return

    if not mt5.initialize():
        print("MT5 gagal")
        return

    if has_open_position():
        print("Masih ada posisi")
        mt5.shutdown()
        return

    df_entry = get_data(mt5.TIMEFRAME_M5)
    df_htf = get_data(mt5.TIMEFRAME_M15)

    signal = get_trade_signal(df_entry, df_htf, session)

    if signal:
        sl, tp = calculate_sl_tp(signal, df_entry)
        result = execute_trade(signal, sl, tp)

        msg = f"""
ICT SCALP EXECUTED
Session: {session}
Signal: {signal}
SL: {sl}
TP: {tp}
"""
        print(msg)
        send_telegram(msg)

    else:
        print("No valid setup")

    mt5.shutdown()

# =========================
if __name__ == "__main__":
    run()
