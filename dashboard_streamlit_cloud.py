import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BTC Grid Bot Dashboard", layout="wide")
st.title("📊 BTC Grid Bot Dashboard (Streamlit Cloud)")

# ======= CREDENZIALI GOOGLE DA streamlit.secrets =======
try:
    credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(credentials_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(st.secrets["GOOGLE_SHEET_NAME"]).worksheet("Foglio1")
    data = sheet.get_all_records()
except Exception as e:
    st.error(f"❌ Errore connessione Google Sheets: {e}")
    st.stop()

# ======= VISUALIZZAZIONE DATI =======
df = pd.DataFrame(data)

if df.empty or df.shape[0] == 0:
    st.warning("📭 Nessun dato disponibile nel foglio Google.")
else:
    try:
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