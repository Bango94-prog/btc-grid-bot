import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# Percorso file credenziali (come prima)
CREDENTIALS_FILE = "/etc/secrets/bubbly-dominion-458720-p4-44cd6a5d8190.json"
SHEET_NAME = "BTC_Grid_Data"
FOGLIO_REGISTRO = "Registro"

# Controllo se file credenziali esiste
if not os.path.exists(CREDENTIALS_FILE):
    st.error(f"Errore: file credenziali non trovato: {CREDENTIALS_FILE}")
    st.stop()

# Connessione a Google Sheet
def connetti_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME)

st.title("Dashboard BTC Grid Bot")

try:
    sheet = connetti_google_sheet().worksheet(FOGLIO_REGISTRO)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Converti la colonna qty_btc in stringhe per usare .str.replace senza errori
    if "qty_btc" in df.columns:
        df["qty_btc"] = df["qty_btc"].astype(str).str.replace(",", ".")
        df["qty_btc"] = pd.to_numeric(df["qty_btc"], errors="coerce")

    st.dataframe(df)

except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
