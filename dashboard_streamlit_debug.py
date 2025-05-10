
import os
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "BTC_Grid_Data")
WORKSHEET_NAME = "Foglio1"
CREDENTIALS_PATH = "/etc/secrets/bubbly-dominion-458720-p4-44cd6a5d8190.json"

st.title("DEBUG Dashboard - Verifica Connessione Google Sheets")

try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)
    data = sheet.get_all_records()
    
    if data:
        df = pd.DataFrame(data)
        st.success("✅ Connessione riuscita. Dati letti:")
        st.dataframe(df)
    else:
        st.warning("⚠️ Connessione riuscita, ma nessun dato presente nel foglio.")
except Exception as e:
    st.error(f"❌ Errore nella connessione o lettura del foglio: {e}")
