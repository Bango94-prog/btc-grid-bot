import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd  # IMPORTA QUI PANDAS
import matplotlib.pyplot as plt  # IMPORTA matplotlib

# Leggi il segreto dallo streamlit secrets
GOOGLE_SHEET_NAME = "BTC_Grid_Data"
FOGLIO_REGISTRO = "Registro"

# Decodifica il JSON dalle secrets
credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
credentials_dict = json.loads(credentials_json)

# Crea credenziali con i permessi giusti
scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

# Crea client gspread
client = gspread.authorize(credentials)

@st.cache_data
def carica_dati_registro():
    sheet = client.open(GOOGLE_SHEET_NAME).worksheet(FOGLIO_REGISTRO)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def calcola_patrimonio(df, prezzo_btc_attuale):
    btc_acquistato = df.loc[df['tipo'] == 'acquisto', 'qty_btc'].sum()
    btc_venduto = df.loc[df['tipo'] == 'vendita', 'qty_btc'].sum()
    btc_netto = btc_acquistato - btc_venduto

    usdc_spesi = df.loc[df['tipo'] == 'acquisto', 'valore_usdc'].sum()
    usdc_ricevuti = df.loc[df['tipo'] == 'vendita', 'valore_usdc'].sum()
    usdc_netto = usdc_ricevuti - usdc_spesi

    patrimonio = btc_netto * prezzo_btc_attuale + usdc_netto

    return btc_netto, usdc_netto, patrimonio

def grafico_interesse_composto(df):
    # Controllo e conversione colonna timestamp in datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    df = df.sort_values('timestamp')

    # Controllo presenza colonna profitto
    if 'profitto' not in df.columns:
        st.error("La colonna 'profitto' non è presente nel dataset.")
        return

    df['profitto_cumulato'] = df['profitto'].cumsum()

    plt.figure(figsize=(10,5))
    plt.plot(df['timestamp'], df['profitto_cumulato'], marker='o', linestyle='-')
    plt.title("Andamento profitto netto cumulato")
    plt.xlabel("Data")
    plt.ylabel("Profitto netto cumulato (USDC)")
    plt.grid(True)
    st.pyplot(plt)

def main():
    st.sidebar.header("Impostazioni")
    prezzo_btc_attuale = st.sidebar.number_input("Prezzo BTC attuale (USDC)", value=28000.0, step=100.0)

    st.write(f"### Prezzo BTC attuale impostato: {prezzo_btc_attuale:.2f} USDC")

    # Carica dati Registro
    df_registro = carica_dati_registro()
    if df_registro.empty:
        st.warning("Nessun dato trovato nel foglio Registro.")
        return

    st.write("### Dati estratti dal foglio Registro")
    st.dataframe(df_registro)

    # Calcola patrimonio
    btc, usdc, patrimonio = calcola_patrimonio(df_registro, prezzo_btc_attuale)

    st.write(f"**BTC netto posseduto:** {btc:.6f} BTC")
    st.write(f"**USDC netto disponibile:** {usdc:.2f} USDC")
    st.write(f"**Patrimonio totale stimato:** {patrimonio:.2f} USDC")

    # Grafico andamento profitto netto cumulato
    grafico_interesse_composto(df_registro)

if __name__ == "__main__":
    main()
