import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.title("Dashboard BTC Grid Bot")

# Configurazioni
GOOGLE_SHEET_NAME = "BTC_Grid_Data"
FOGLIO_REGISTRO = "Registro"

@st.cache_data(ttl=300)
def carica_dati_registro():
    # Carica credenziali da st.secrets (stringa JSON)
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict)
    client = gspread.authorize(creds)

    # Apri foglio e leggi dati
    sheet = client.open(GOOGLE_SHEET_NAME).worksheet(FOGLIO_REGISTRO)
    records = sheet.get_all_records()

    # Converte in DataFrame e sistema le date
    df = pd.DataFrame(records)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def calcola_patrimonio(df, prezzo_btc_attuale):
    # Somma BTC acquistato meno BTC venduto
    btc_acquistato = df.loc[df['tipo'] == 'acquisto', 'qty_btc'].sum()
    btc_venduto = df.loc[df['tipo'] == 'vendita', 'qty_btc'].sum()
    btc_netto = btc_acquistato - btc_venduto

    # Calcolo USDC netto dal registro: somma profitti + saldo teorico USDC
    usdc_spesi = df.loc[df['tipo'] == 'acquisto', 'valore_usdc'].sum()
    usdc_ricevuti = df.loc[df['tipo'] == 'vendita', 'valore_usdc'].sum()
    usdc_netto = usdc_ricevuti - usdc_spesi

    # Valore totale (BTC * prezzo attuale + USDC netto)
    patrimonio = btc_netto * prezzo_btc_attuale + usdc_netto

    return btc_netto, usdc_netto, patrimonio

def grafico_interesse_composto(df):
    # Ordina per data e calcola patrimonio cumulativo considerando profitto netto
    df = df.sort_values('timestamp')
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
