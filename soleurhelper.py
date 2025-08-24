import requests
import time
import os

# ==== ANSI colors (works in most terminals) ====
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ==== Terminal helpers ====
def clear_terminal():
    # Clear terminal for Windows or Linux/Mac
    os.system('cls' if os.name == 'nt' else 'clear')

# ==== Data ====
def get_spot_price(symbol="SOLEUR"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return float(data["price"])

# ==== Indicators ====
def moving_average(prices, period=20):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    # Use last `period` deltas
    for i in range(-period, 0):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calculate_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow + signal:
        return None, None

    def ema(series, period):
        k = 2.0 / (period + 1.0)
        out = []
        for i, v in enumerate(series):
            if i == 0:
                out.append(v)
            else:
                out.append(v * k + out[-1] * (1 - k))
        return out

    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    # Align lengths (use last len(ema_slow))
    macd_line_series = [f - s for f, s in zip(ema_fast[-len(ema_slow):], ema_slow)]
    signal_line_series = ema(macd_line_series, signal)
    return macd_line_series[-1], signal_line_series[-1]

# ==== Decision rules ====
def get_action(price, ma20, rsi14, macd, macd_signal):
    # Tunable thresholds
    rsi_buy_th = 35
    rsi_sell_th = 65

    if price > ma20 and rsi14 is not None and rsi14 < rsi_buy_th and macd is not None and macd_signal is not None and macd > macd_signal:
        return "BUY ✅", GREEN
    if price < ma20 and rsi14 is not None and rsi14 > rsi_sell_th and macd is not None and macd_signal is not None and macd < macd_signal:
        return "SELL ❌", RED
    return "HOLD ⚖️", YELLOW

# ==== UI ====
def sparkline(prices):
    chars = "▁▂▃▄▅▆▇█"
    lo, hi = min(prices), max(prices)
    if hi == lo:
        return "▁" * len(prices)
    out = []
    for p in prices:
        idx = int((p - lo) / (hi - lo) * (len(chars) - 1))
        out.append(chars[idx])
    return "".join(out)

def display(symbol, prices, action, color, ma20, rsi14, macd, macd_signal):
    latest = prices[-1]
    print(f"{CYAN}{symbol} Spot (Binance) – Real-time Helper{RESET}")
    print(f"Price History: {sparkline(prices)}")
    print(f"Current Price: {latest:.4f}")
    if ma20 is not None:
        print(f"MA20: {ma20:.4f}")
    if rsi14 is not None:
        print(f"RSI14: {rsi14:.2f}")
    if macd is not None and macd_signal is not None:
        print(f"MACD: {macd:.4f} | Signal: {macd_signal:.4f}")
    print(f"Suggestion: {color}{action}{RESET}")

# ==== Main loop ====
def soleur_helper(symbol="SOLEUR", interval=0.5, history=60):
    prices = []
    last_action = None
    print(f"Starting {symbol} helper (updates every {interval}s)…")
    while True:
        try:
            price = get_spot_price(symbol)
        except Exception as e:
            print(f"Fetch error: {e}. Retrying…")
            time.sleep(interval)
            continue

        prices.append(price)
        if len(prices) > history:
            prices.pop(0)

        ma20 = moving_average(prices, 20)
        rsi14 = calculate_rsi(prices, 14)
        macd, macd_sig = calculate_macd(prices)

        # Need enough data for indicators
        if ma20 is None or rsi14 is None or macd is None or macd_sig is None:
            clear_terminal()
            print(f"Collecting data… ({len(prices)}/{max(26+9, 20)})")
            time.sleep(interval)
            continue

        action, color = get_action(price, ma20, rsi14, macd, macd_sig)

        # Alert on change
        if action != last_action:
            print("\a", end="")  # terminal bell
            last_action = action

        clear_terminal()
        display(symbol, prices, action, color, ma20, rsi14, macd, macd_sig)
        time.sleep(interval)

if __name__ == "__main__":
    # Runs immediately for SOLEUR, updating ~2 times/second.
    soleur_helper()
