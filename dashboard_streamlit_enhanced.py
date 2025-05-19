import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BTC Grid Bot Dashboard", layout="wide", page_icon="📊")
st.markdown("<h1 style='text-align: center; color: white;'>📊 BTC Grid Bot Dashboard</h1>", unsafe_allow_html=True)

# ======= CREDENZIALI GOOGLE DA streamlit.secrets =======
try:
    credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(credentials_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # Prendo il nome del foglio da secrets, default a "Registro"
    sheet_name = st.secrets.get("GOOGLE_SHEET_TAB", "Registro")
    
    sheet = client.open(st.secrets["GOOGLE_SHEET_NAME"]).worksheet(sheet_name)
    data = sheet.get_all_records()
except Exception as e:
    st.error(f"❌ Errore connessione Google Sheets: {e}")
    st.stop()

# ======= PREPARAZIONE DATI =======
df = pd.DataFrame(data)

if df.empty or df.shape[0] == 0:
    st.warning("📭 Nessun dato disponibile nel foglio Google.")
    st.stop()

df.columns = [col.lower().strip() for col in df.columns]
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["capitale_totale"] = pd.to_numeric(df["capitale_totale"], errors="coerce")
df["profitto_netto"] = pd.to_numeric(df["profitto_netto"], errors="coerce")
df["btc_qty"] = pd.to_numeric(df.get("btc_qty", 0), errors="coerce")
df["usdt_qty"] = pd.to_numeric(df.get("usdt_qty", 0), errors="coerce")
df = df.dropna(subset=["timestamp", "capitale_totale", "profitto_netto"])
df = df.sort_values("timestamp")
initial_capital = 500
df["capitale_composito"] = initial_capital + df["profitto_netto"].cumsum()
df["profitto_percentuale"] = 100 * (df["capitale_totale"] - initial_capital) / initial_capital

latest = df.iloc[-1]
btc_qty = latest["btc_qty"]
usdc_qty = latest["usdt_qty"]
total_cap = latest["capitale_totale"]
profitto_percentuale = latest["profitto_percentuale"]

# ======= LAYOUT AVANZATO =======
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Capitale Totale", f"{total_cap:.2f} USDC")
col2.metric("📈 Profitto Netto", f"{latest['profitto_netto']:.2f} USDC")
col3.metric("🔄 BTC", f"{btc_qty:.6f}")
col4.metric("💵 USDC", f"{usdc_qty:.2f}")

st.markdown("---")

# ======= ALERT su RISERVA < 100 USDC =======
if usdc_qty < 100:
    st.error("⚠️ Attenzione: la riserva USDC è scesa sotto i 100 USDC!")

# ======= GRAFICO LINEA =======
st.subheader("📊 Capitale con Interesse Composto")
range_selector = st.selectbox("Intervallo storico:", ["Tutto", "Ultimi 7 giorni", "Ultimi 30 giorni"])
if range_selector == "Ultimi 7 giorni":
    df_filtered = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=7)]
elif range_selector == "Ultimi 30 giorni":
    df_filtered = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=30)]
else:
    df_filtered = df

st.line_chart(df_filtered.set_index("timestamp")[["capitale_composito"]])

# ======= STORICO OPERAZIONI =======
st.subheader("📄 Storico Operazioni")
st.dataframe(df[::-1], use_container_width=True)
