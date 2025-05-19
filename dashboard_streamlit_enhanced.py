import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd
import matplotlib.pyplot as plt

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
client = gspread.authorize(credentials)

@st.cache_data
def carica_dati_registro():
    sheet = client.open(GOOGLE_SHEET_NAME).worksheet(FOGLIO_REGISTRO)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Pulizia e conversione tipi
    df['qty_btc'] = pd.to_numeric(df['qty_btc'], errors='coerce').fillna(0)
    df['valore_usdc'] = pd.to_numeric(df['valore_usdc'], errors='coerce').fillna(0)
    df['profitto'] = pd.to_numeric(df['profitto'], errors='coerce').fillna(0)
    df['tipo'] = df['tipo'].str.strip().str.lower()
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
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

def grafico_interesse_composto(df, prezzo_btc_attuale):
    df = df.sort_values('timestamp').copy()

    # Calcolo BTC e USDC netti progressivi (interesse composto)
    btc_netto_progressivo = []
    usdc_netto_progressivo = []
    btc_acq_cum = 0
    btc_vend_cum = 0
    usdc_acq_cum = 0
    usdc_vend_cum = 0
    
    for idx, row in df.iterrows():
        if row['tipo'] == 'acquisto':
            btc_acq_cum += row['qty_btc']
            usdc_acq_cum += row['valore_usdc']
        elif row['tipo'] == 'vendita':
            btc_vend_cum += row['qty_btc']
            usdc_vend_cum += row['valore_usdc']
        btc_netto_progressivo.append(btc_acq_cum - btc_vend_cum)
        usdc_netto_progressivo.append(usdc_vend_cum - usdc_acq_cum)
    
    df['btc_netto_progressivo'] = btc_netto_progressivo
    df['usdc_netto_progressivo'] = usdc_netto_progressivo
    
    # Calcolo patrimonio progressivo (BTC * prezzo + USDC)
    df['patrimonio_progressivo'] = df['btc_netto_progressivo'] * prezzo_btc_attuale + df['usdc_netto_progressivo']

    plt.figure(figsize=(10,5))
    plt.plot(df['timestamp'], df['patrimonio_progressivo'], marker='o', linestyle='-', color='blue')
    plt.title("Andamento patrimonio totale con interesse composto")
    plt.xlabel("Data")
    plt.ylabel("Patrimonio stimato (USDC)")
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

    # Mostra dati grezzi recenti (opzionale)
    st.write("### Ultime 10 operazioni")
    st.dataframe(df_registro.sort_values('timestamp', ascending=False).head(10))

    # Calcola patrimonio e profitto netto totale
    btc, usdc, patrimonio = calcola_patrimonio(df_registro, prezzo_btc_attuale)
    profitto_totale = df_registro['profitto'].sum()

    st.write(f"**BTC netto posseduto:** {btc:.6f} BTC")
    st.write(f"**USDC netto disponibile:** {usdc:.2f} USDC")
    st.write(f"**Profitto netto totale:** {profitto_totale:.2f} USDC")
    st.write(f"**Patrimonio totale stimato:** {patrimonio:.2f} USDC")

    # Grafico interesse composto patrimonio
    grafico_interesse_composto(df_registro, prezzo_btc_attuale)

if __name__ == "__main__":
    main()
