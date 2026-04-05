#!/usr/bin/env python3
"""
generate_sample_data.py
Buat sample CSV trade log untuk testing tanpa perlu MT5.
"""

import csv
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path.home() / "mt5_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "trade_log.csv"

SYMBOLS  = ["XAUUSD", "GBPUSD", "EURUSD", "USDJPY", "GBPJPY", "NAS100"]
SESSIONS = ["London-Killzone", "NY-Killzone", "London", "NewYork", "Asia-Killzone"]
TYPES    = ["BUY", "SELL"]

def generate_trades(n=20, days_back=30):
    trades = []
    now = datetime.now()

    for i in range(n):
        symbol    = random.choice(SYMBOLS)
        ttype     = random.choice(TYPES)
        volume    = round(random.choice([0.01, 0.02, 0.05, 0.10]), 2)
        session   = random.choice(SESSIONS)
        open_time = now - timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        duration  = random.randint(5, 480)
        close_time = open_time + timedelta(minutes=duration)

        open_price  = round(random.uniform(1.05, 1.30), 5)
        pip_move    = random.uniform(-50, 100)  # bias ke profit
        close_price = round(open_price + pip_move * 0.0001, 5)

        # Profit/loss berdasarkan direction dan pip move
        if ttype == "BUY":
            profit = round((close_price - open_price) * volume * 100000 * 0.1, 2)
        else:
            profit = round((open_price - close_price) * volume * 100000 * 0.1, 2)

        commission = round(-volume * 3.5, 2)
        swap       = round(random.uniform(-0.5, 0.0), 2)
        net_profit = round(profit + commission + swap, 2)

        trades.append({
            "ticket":       1000 + i,
            "open_time":    open_time.strftime("%Y.%m.%d %H:%M"),
            "close_time":   close_time.strftime("%Y.%m.%d %H:%M"),
            "symbol":       symbol,
            "type":         ttype,
            "volume":       volume,
            "open_price":   open_price,
            "close_price":  close_price,
            "sl":           round(open_price - 0.0050, 5),
            "tp":           round(open_price + 0.0100, 5),
            "profit":       profit,
            "commission":   commission,
            "swap":         swap,
            "net_profit":   net_profit,
            "duration_min": duration,
            "rr_actual":    0,
            "session":      session,
            "comment":      "ICT OB",
        })

    return trades

def main():
    print(f"Generating sample trades -> {OUTPUT_FILE}")
    trades = generate_trades(n=25, days_back=7)

    fieldnames = [
        "ticket", "open_time", "close_time", "symbol", "type",
        "volume", "open_price", "close_price", "sl", "tp",
        "profit", "commission", "swap", "net_profit",
        "duration_min", "rr_actual", "session", "comment"
    ]

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)

    wins = len([t for t in trades if t["net_profit"] > 0])
    total_pnl = sum(t["net_profit"] for t in trades)
    print(f"Generated {len(trades)} trades | {wins} wins | Net PnL: {total_pnl:.2f}")
    print(f"File: {OUTPUT_FILE}")
    print("\nTest sekarang dengan:")
    print(f"  python3 ~/mt5_openclaw/python/trade_summary.py --period week --dry-run")

if __name__ == "__main__":
    main()
