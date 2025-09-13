import os
import time
import csv
from datetime import datetime
import requests
import MetaTrader5 as mt5
from flask import Flask
from threading import Thread

# ----------------------------- CONFIGURAÇÃO TELEGRAM -----------------------------
TELEGRAM_BOT_TOKEN = os.getenv("18263528543:AAGsY40ZAAecdY09uFxhzxOG3VAhFbjl6A") or "18263528543:AAGsY40ZAAecdY09uFxhzxOG3VAhFbjl6A"
TELEGRAM_CHAT_ID = os.getenv("1381207189") or "1381207189"

class TelegramBot:
    def __init__(self):
        self.TOKEN = TELEGRAM_BOT_TOKEN
        self.CHAT_ID = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.TOKEN}"
    
    def send_signal(self, symbol, direction, entry, sl, tp1, tp2, timeframe="M15"):
        message = f"""
🟢 <b>SINAL DE TRADE CONFIRMADO</b> 🟢

📈 <b>Par:</b> {symbol}
🎯 <b>Direção:</b> {direction}
💰 <b>Entrada:</b> {entry}
🛑 <b>Stop Loss:</b> {sl}
✅ <b>Take Profit 1:</b> {tp1}
✅ <b>Take Profit 2:</b> {tp2}

⏰ <b>Horário:</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
📊 <b>Timeframe:</b> {timeframe}
"""
        self._send_message(message)

    def _send_message(self, message):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": self.CHAT_ID, "text": message, "parse_mode": "HTML"}
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Erro Telegram: {e}")

telegram_bot = TelegramBot()

# ----------------------------- CONFIGURAÇÃO MT5 -----------------------------
MT5_PATH = os.getenv("MT5_PATH") or r"C:\Program Files\XM Global MT5\terminal64.exe"
ACCOUNT_LOGIN = int(os.getenv("MT5_LOGIN") or 333652897)
ACCOUNT_PASSWORD = os.getenv("MT5_PASSWORD") or "Joao!01596"
ACCOUNT_SERVER = os.getenv("MT5_SERVER") or "XMGlobal-MT5 9"

SYMBOL = "BTCUSD"
LOT_MIN = 0.01
LOT_MAX = 10.0
TIMEFRAME = mt5.TIMEFRAME_M15
SLC_PIPS = 300
TP_PIPS = 600
LOOP_INTERVAL = 60  # segundos

TRADE_LOG_CSV = "trades_log.csv"

# ----------------------------- FUNÇÕES MT5 -----------------------------
def init_mt5():
    if not mt5.initialize(MT5_PATH):
        print(f"Falha ao iniciar MT5: {mt5.last_error()}")
        return False
    if not mt5.login(ACCOUNT_LOGIN, ACCOUNT_PASSWORD, ACCOUNT_SERVER):
        print(f"Falha ao logar MT5: {mt5.last_error()}")
        mt5.shutdown()
        return False
    print("✅ Conectado ao MT5")
    return True

def symbol_check(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"Símbolo {symbol} não encontrado no MT5")
    if not info.visible:
        mt5.symbol_select(symbol, True)
    return info

def pips_to_price(symbol_info, pips):
    return pips * symbol_info.point

def write_trade_log(row):
    header = ["timestamp","symbol","direction","entry","sl","tp1","tp2"]
    new_file = not os.path.exists(TRADE_LOG_CSV)
    with open(TRADE_LOG_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(header)
        writer.writerow(row)

# ----------------------------- LÓGICA DE TRADE -----------------------------
def simple_breakout_signal(symbol):
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 6)
    if rates is None or len(rates) < 6:
        return None
    highs = [r[2] for r in rates[2:6]]
    lows = [r[3] for r in rates[2:6]]
    curr = rates[0]
    if curr[4] > max(highs):
        return "BUY"
    if curr[4] < min(lows):
        return "SELL"
    return None

def place_market_order(symbol, lot, order_type, sl_price, tp_price):
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 20,
        "magic": 20250913,
        "comment": "BTC_RENDER_BOT",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    return mt5.order_send(request)

def bot_loop():
    if not init_mt5():
        return
    symbol_info = symbol_check(SYMBOL)
    while True:
        signal = simple_breakout_signal(SYMBOL)
        if signal is None:
            time.sleep(LOOP_INTERVAL)
            continue

        tick = mt5.symbol_info_tick(SYMBOL)
        lot = LOT_MIN  # você pode adicionar cálculo de lot baseado em risco

        if signal == "BUY":
            sl_price = tick.bid - pips_to_price(symbol_info, SLC_PIPS)
            tp_price = tick.bid + pips_to_price(symbol_info, TP_PIPS)
            order_type = mt5.ORDER_TYPE_BUY
        else:
            sl_price = tick.ask + pips_to_price(symbol_info, SLC_PIPS)
            tp_price = tick.ask - pips_to_price(symbol_info, TP_PIPS)
            order_type = mt5.ORDER_TYPE_SELL

        result = place_market_order(SYMBOL, lot, order_type, sl_price, tp_price)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Ordem falhou: {result}")
        else:
            print(f"{datetime.now()} - Ordem enviada: {signal} {tick.last}")
            telegram_bot.send_signal(SYMBOL, signal, round(tick.last,2), round(sl_price,2), round(tp_price,2), round(tp_price*1.5,2))
            write_trade_log([datetime.now(), SYMBOL, signal, round(tick.last,2), round(sl_price,2), round(tp_price,2), round(tp_price*1.5,2)])

        time.sleep(LOOP_INTERVAL)

# ----------------------------- FLASK WEB SERVICE -----------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot MT5 Render rodando! ✅"

if __name__ == "__main__":
    Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
