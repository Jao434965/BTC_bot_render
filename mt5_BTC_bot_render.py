import time
import csv
from datetime import datetime
import requests
import random

# ----------------------------- TELEGRAM -----------------------------
TELEGRAM_BOT_TOKEN = "18263528543:AAGsY40ZAAecdY09uFxhzxOG3VAhFbjl6A"
TELEGRAM_CHAT_ID = "1381207189"

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

# ----------------------------- LOG -----------------------------
LOG_FILE = "trades_log.csv"
... 
... def write_trade_log(row):
...     header = ["timestamp","symbol","direction","entry","sl","tp1","tp2"]
...     new_file = not os.path.exists(LOG_FILE)
...     with open(LOG_FILE, "a", newline="") as f:
...         writer = csv.writer(f)
...         if new_file:
...             writer.writerow(header)
...         writer.writerow(row)
... 
... # ----------------------------- SIMULAÇÃO DE SINAIS -----------------------------
... SYMBOL = "BTCUSD"
... TIMEFRAME = "M15"
... 
... def generate_signal():
...     """Simula sinais de trade BUY ou SELL"""
...     direction = random.choice(["BUY", "SELL"])
...     price = round(random.uniform(30000, 40000), 2)
...     sl = price - 200 if direction == "BUY" else price + 200
...     tp1 = price + 400 if direction == "BUY" else price - 400
...     tp2 = price + 600 if direction == "BUY" else price - 600
...     return direction, price, sl, tp1, tp2
... 
... # ----------------------------- LOOP PRINCIPAL -----------------------------
... LOOP_INTERVAL = 60  # segundos
... 
... while True:
...     direction, entry, sl, tp1, tp2 = generate_signal()
...     
...     # Envia para Telegram
...     telegram_bot.send_signal(SYMBOL, direction, entry, sl, tp1, tp2, TIMEFRAME)
...     
...     # Salva log
...     write_trade_log([datetime.now(), SYMBOL, direction, entry, sl, tp1, tp2])
...     
...     print(f"{datetime.now()} - Sinal enviado: {direction} {entry}")
...     
...     time.sleep(LOOP_INTERVAL)

