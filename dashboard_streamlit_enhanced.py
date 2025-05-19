import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BTC Grid Bot Dashboard", layout="wide", page_icon="📊")
st.title("📊 BTC Grid Bot Dashboard")

# Connessione a Google Sheets
try:
    credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(credentials_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(st.secrets["GOOGLE_SHEET_NAME"]).worksheet("Registro")
    data = sheet.get_all_records()
except Exception as e:
    st.error(f"❌ Errore connessione Google Sheets: {e}")
    st.stop()

df = pd.DataFrame(data)

if df.empty:
    st.warning("📭 Nessun dato disponibile nel foglio Google 'Registro'.")
    st.stop()

# Conversione colonne
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["qty_btc"] = pd.to_numeric(df["qty_btc"], errors="coerce")
df["valore_usdc"] = pd.to_numeric(df["valore_usdc"], errors="coerce")
df["profitto"] = pd.to_numeric(df["profitto"], errors="coerce")
df["prezzo"] = pd.to_numeric(df["prezzo"], errors="coerce")

# Ordina per data
df = df.sort_values("timestamp")

# Determinare segno quantità in base a tipo operazione (ad esempio "acquisto" o "vendita")
# Qui devi adattare in base a come hai definito il tipo in 'tipo'
def segno_qty(row):
    if row['tipo'].lower() in ['acquisto', 'buy']:
        return 1
    elif row['tipo'].lower() in ['vendita', 'sell']:
        return -1
    else:
        return 0

df['segno'] = df.apply(segno_qty, axis=1)

# Calcolo saldo BTC e USDC correnti
df['qty_btc_signed'] = df['qty_btc'] * df['segno']
df['valore_usdc_signed'] = df['valore_usdc'] * (-df['segno'])  # supponendo che se compro BTC esco USDC, e viceversa

saldo_btc = df['qty_btc_signed'].sum()
saldo_usdc = df['valore_usdc_signed'].sum()

ultimo_prezzo = df["prezzo"].iloc[-1] if not df["prezzo"].empty else 0

capitale_totale = saldo_usdc + saldo_btc * ultimo_prezzo

# Interesse composto a partire da capitale iniziale (es. 500 USDC)
capitale_iniziale = 500
df["capitale_composito"] = capitale_iniziale + df["profitto"].cumsum()

# Visualizzazione metriche
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Capitale Totale", f"{capitale_totale:.2f} USDC")
col2.metric("📈 Profitto Netto Totale", f"{df['profitto'].sum():.2f} USDC")
col3.metric("🔄 BTC Totale", f"{saldo_btc:.6f}")
col4.metric("💵 USDC Totale", f"{saldo_usdc:.2f}")

st.markdown("---")

# Grafico interesse composto con filtro periodo
st.subheader("📊 Capitale con Interesse Composto")
range_selector = st.selectbox("Intervallo storico:", ["Tutto", "Ultimi 7 giorni", "Ultimi 30 giorni"])
if range_selector == "Ultimi 7 giorni":
    df_filtered = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=7)]
elif range_selector == "Ultimi 30 giorni":
    df_filtered = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=30)]
else:
    df_filtered = df

st.line_chart(df_filtered.set_index("timestamp")[["capitale_composito"]])

# Storico operazioni
st.subheader("📄 Storico Operazioni")
st.dataframe(df[::-1], use_container_width=True)
