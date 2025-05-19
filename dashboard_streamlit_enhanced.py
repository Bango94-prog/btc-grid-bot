import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BTC Grid Bot Dashboard", layout="wide", page_icon="📊")
st.title("📊 BTC Grid Bot Dashboard")

# Connessione Google Sheets
try:
    credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(credentials_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(st.secrets["GOOGLE_SHEET_NAME"]).worksheet("Registro")
    data = sheet.get_all_records()
except Exception as e:
    st.error(f"Errore connessione Google Sheets: {e}")
    st.stop()

df = pd.DataFrame(data)

if df.empty:
    st.warning("Nessun dato disponibile nel foglio 'Registro'.")
    st.stop()

# Pulizia dati
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["qty_btc"] = pd.to_numeric(df["qty_btc"].str.replace(",", "."), errors="coerce")  # attenzione alle virgole
df["valore_usdc"] = pd.to_numeric(df["valore_usdc"].str.replace(",", "."), errors="coerce")
df["profitto"] = pd.to_numeric(df["profitto"].str.replace(",", "."), errors="coerce")
df["prezzo"] = pd.to_numeric(df["prezzo"].str.replace(",", "."), errors="coerce")
df = df.sort_values("timestamp")

# Funzioni per segni corretti
def btc_signed(row):
    if row['tipo'].lower() == 'acquisto':
        return row['qty_btc']          # BTC acquistati: saldo BTC + 
    elif row['tipo'].lower() == 'vendita':
        return -row['qty_btc']         # BTC venduti: saldo BTC -
    else:
        return 0

def usdc_signed(row):
    if row['tipo'].lower() == 'acquisto':
        return -row['valore_usdc']     # USDC spesi per comprare BTC: saldo USDC -
    elif row['tipo'].lower() == 'vendita':
        return row['valore_usdc']      # USDC ricevuti vendendo BTC: saldo USDC +
    else:
        return 0

df['btc_signed'] = df.apply(btc_signed, axis=1)
df['usdc_signed'] = df.apply(usdc_signed, axis=1)

# Saldi attuali
saldo_btc = df['btc_signed'].sum()
saldo_usdc = df['usdc_signed'].sum()

# Prezzo corrente = prezzo dell'ultima transazione
prezzo_corrente = df['prezzo'].iloc[-1]

# Capitale totale = USDC + BTC * prezzo_corrente
capitale_totale = saldo_usdc + saldo_btc * prezzo_corrente

# Profitto netto totale (somma dei profitti nelle vendite)
profitto_totale = df['profitto'].sum()

# Interesse composto basato su profitto cumulato, capitale iniziale 500 USDC (modifica se vuoi)
capitale_iniziale = 500
df['profitto_cumulato'] = df['profitto'].cumsum()
df['capitale_composto'] = capitale_iniziale + df['profitto_cumulato']

# Layout dashboard
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Capitale Totale", f"{capitale_totale:.2f} USDC")
col2.metric("📈 Profitto Netto Totale", f"{profitto_totale:.2f} USDC")
col3.metric("🔄 BTC Totale", f"{saldo_btc:.6f}")
col4.metric("💵 USDC Totale", f"{saldo_usdc:.2f}")

st.markdown("---")

# Grafico interesse composto con filtro intervalli
st.subheader("📊 Capitale con Interesse Composto")
range_selector = st.selectbox("Intervallo storico:", ["Tutto", "Ultimi 7 giorni", "Ultimi 30 giorni"])

if range_selector == "Ultimi 7 giorni":
    df_filtered = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=7)]
elif range_selector == "Ultimi 30 giorni":
    df_filtered = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=30)]
else:
    df_filtered = df

st.line_chart(df_filtered.set_index("timestamp")[["capitale_composto"]])

# Storico operazioni
st.subheader("📄 Storico Operazioni")
st.dataframe(df[::-1], use_container_width=True)

# DEBUG per controllare segni (opzionale)
st.subheader("DEBUG - Controllo Segni")
st.dataframe(df[['timestamp', 'tipo', 'qty_btc', 'btc_signed', 'valore_usdc', 'usdc_signed']].tail(10))
