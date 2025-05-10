import os
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ===== CONFIG =====
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "BTC_Grid_Data")
WORKSHEET_NAME = "Foglio1"
CREDENTIALS_PATH = "/etc/secrets/bubbly-dominion-458720-p4-44cd6a5d8190.json"

# ===== CONNESSIONE GOOGLE SHEET =====
def carica_dati_da_google_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Errore connessione Google Sheets: {e}")
        return pd.DataFrame()

# ===== DASHBOARD =====
st.set_page_config(page_title="BTC Grid Bot Dashboard", layout="wide")
st.title("📊 BTC Grid Bot Dashboard")

df = carica_dati_da_google_sheets()

if df.empty or df.shape[0] == 0:
    st.warning("📭 Nessun dato disponibile nel foglio Google.")
else:
    try:
        # Pulizia e formattazione
        df.columns = [col.lower().strip() for col in df.columns]
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["capitale_totale"] = pd.to_numeric(df["capitale_totale"], errors="coerce")
        df["profitto_netto"] = pd.to_numeric(df["profitto_netto"], errors="coerce")

        df = df.dropna(subset=["timestamp", "capitale_totale", "profitto_netto"])
        df = df.sort_values("timestamp")

        st.subheader("💰 Stato Attuale")
        latest = df.iloc[-1]
        st.metric("Capitale Totale", f'{latest["capitale_totale"]:.2f} USDC')
        st.metric("BTC", f'{latest.get("btc_qty", 0):.6f}')
        st.metric("USDC", f'{latest.get("usdt_qty", 0):.2f}')
        st.metric("Ultimo profitto", f'{latest["profitto_netto"]:.2f} USDC')

        st.subheader("📈 Crescita del Capitale (Interesse Composto)")
        df["capitale_composito"] = 500 + df["profitto_netto"].cumsum()
        st.line_chart(df.set_index("timestamp")[["capitale_composito"]])

        st.subheader("📄 Storico Operazioni")
        st.dataframe(df[::-1], use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Errore durante la visualizzazione dei dati: {e}")