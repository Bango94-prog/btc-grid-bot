
# BTC Grid Bot con Griglia Dinamica ATR, Notifiche su Profitto, Reinvestimento e Riserva
import requests
import ccxt
import pandas as pd
import time
from datetime import datetime

# === CONFIGURAZIONE ===
API_KEY = ''  # Inserisci qui la tua API Key quando pronta
API_SECRET = ''

symbol = 'BTC/USDC'
capital_total = 500
capital_grid = 400
capital_reserve = 100
emergency_threshold = 56000  # BTC sotto i 56.000€ attiva riserva

min_grid_pct = 0.0075  # 0.75%
max_grid_pct = 0.035   # 3.5%

token = 'INSERISCI_IL_TUO_TOKEN_TELEGRAM'
chat_id = 'INSERISCI_LA_TUA_CHAT_ID_TELEGRAM'

# === Inizializzazione exchange ===
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

# === Funzione Telegram ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Errore Telegram:", e)

# === Calcolo ATR ===
def get_atr(symbol, timeframe='1h', period=24):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = df['TR'].rolling(window=period).mean().iloc[-1]
    return atr

# === Costruzione Griglia Dinamica ===
def build_grid(price):
    atr = get_atr(symbol)
    step_pct = max(min_grid_pct, min(max_grid_pct, atr / price))
    levels = []
    for i in range(-5, 6):  # 11 livelli
        levels.append(price * (1 + step_pct * i))
    return levels, step_pct

# === Trading Loop ===
def run_bot():
    invested_orders = {}
    usdt_balance = capital_grid
    reserve_used = False
    while True:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        
        # Griglia dinamica
        grid, grid_step = build_grid(price)
        
        # Controlla trigger emergenza
        if price < emergency_threshold and not reserve_used:
            send_telegram(f"⚠️ Prezzo BTC sotto {emergency_threshold}€. Attivata la riserva!")
            usdt_balance += capital_reserve
            reserve_used = True

        # Simulazione: check se un ordine virtuale è stato riempito
        for level in grid:
            if level < price * 0.995 and usdt_balance >= level * 0.001:
                buy_price = level
                amount = (usdt_balance * 0.1) / buy_price
                usdt_balance -= amount * buy_price
                invested_orders[buy_price] = amount
                print(f"Comprato a {buy_price:.2f} BTC")
            
            elif level > price * 1.005:
                for buy_price in list(invested_orders):
                    if level > buy_price * (1 + grid_step):
                        sell_price = level
                        amount = invested_orders.pop(buy_price)
                        gross = sell_price * amount
                        net = gross * 0.998  # fee 0.1% * 2
                        profit = net - (buy_price * amount)
                        usdt_balance += net
                        send_telegram(
                            f"✅ Profitto Realizzato:
Acquisto: {buy_price:.2f} USDT
Vendita: {sell_price:.2f} USDT
Profitto netto: {profit:.2f} USDT"
                        )

        print(f"{datetime.now().strftime('%H:%M:%S')} | Prezzo: {price:.2f} | Saldo USDT: {usdt_balance:.2f}")
        time.sleep(60)

# === Avvio ===
send_telegram("🤖 BTC Grid Bot Avviato!")
run_bot()



import gspread
from google.oauth2.service_account import Credentials
import datetime

# Configurazione Google Sheets
SHEET_NAME = "BTC_Grid_Data"
WORKSHEET_NAME = "Foglio1"
CREDENTIALS_FILE = "bubbly-dominion-458720-p4-44cd6a5d8190.json"

# Connessione al foglio Google
def connetti_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    return sheet

# Funzione per aggiornare il foglio
def aggiorna_google_sheet(timestamp, capitale_totale, btc_qty, usdt_qty, profitto_netto):
    try:
        sheet = connetti_google_sheet()
        row = [timestamp, capitale_totale, btc_qty, usdt_qty, profitto_netto]
        sheet.append_row(row)
        print(f"[GOOGLE SHEET] Riga aggiunta: {row}")
    except Exception as e:
        print(f"[ERRORE GOOGLE SHEET] {e}")
