import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configurazioni Google Sheets
SHEET_NAME = "BTC_Grid_Data"
FOGLIO_REGISTRO = "Registro"
CREDENTIALS_FILE = "/etc/secrets/bubbly-dominion-458720-p4-44cd6a5d8190.json"

# Funzione per connettersi al Google Sheet
def connetti_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    return gspread.authorize(creds).open(SHEET_NAME)

# Carico i dati dal foglio Registro
def carica_dati_registro():
    try:
        sheet = connetti_google_sheet().worksheet(FOGLIO_REGISTRO)
        dati = sheet.get_all_records()
        df = pd.DataFrame(dati)

        # Correzione: converti colonne numeriche, prima a stringa, poi replace, poi numerico
        df["qty_btc"] = pd.to_numeric(df["qty_btc"].astype(str).str.replace(",", "."), errors="coerce")
        df["prezzo"] = pd.to_numeric(df["prezzo"].astype(str).str.replace(",", "."), errors="coerce")
        df["valore_usdc"] = pd.to_numeric(df["valore_usdc"].astype(str).str.replace(",", "."), errors="coerce")
        df["fee"] = pd.to_numeric(df["fee"].astype(str).str.replace(",", "."), errors="coerce")
        df["profitto"] = pd.to_numeric(df["profitto"].astype(str).str.replace(",", "."), errors="coerce")

        return df
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return pd.DataFrame()

# Streamlit app
st.title("Registro Operazioni BTC Grid Bot")

df_registro = carica_dati_registro()

if not df_registro.empty:
    st.dataframe(df_registro)
else:
    st.write("Nessun dato disponibile nel foglio Registro.")
