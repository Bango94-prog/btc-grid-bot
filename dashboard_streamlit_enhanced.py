import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd
import matplotlib.pyplot as plt

GOOGLE_SHEET_NAME = "BTC_Grid_Data"
FOGLIO_REGISTRO = "Registro"

credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
credentials_dict = json.loads(credentials_json)

scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
client = gspread.authorize(credentials)

@st.cache_data
def carica_dati_registro():
    sheet = client.open(GOOGLE_SHEET_NAME).worksheet(FOGLIO_REGISTRO)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Normalizza i numeri (virgole → punti decimali)
    cols_da_convertire = ['qty_btc', 'valore_usdc', 'profitto']
    for col in cols_da_convertire:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)

    # Timestamp in formato datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Normalizza la colonna tipo
    df['tipo'] = df['tipo'].str.strip().str.lower()

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

    btc_acq_cum = 0
    btc_vend_cum = 0
    usdc_acq_cum = 0
    usdc_vend_cum = 0

    btc_netto_progressivo = []
    usdc_netto_progressivo = []

    for _, row in df.iterrows():
        if row['tipo'] == 'acquisto':
            btc_acq_cum += row['qty_btc']
            usdc_acq_cum += row['valore_usdc']
        elif row['tipo'] == 'vendita':
            btc_vend_cum += row['qty_btc']
            usdc_vend_cum += row['valore_usdc']

        btc_netto_progressivo.append(btc_acq_cum - btc_vend_cum)
        usdc_netto_progressivo.append(usdc_vend_cum - usdc_acq_cum)

    df['btc_netto'] = btc_netto_progressivo
    df['usdc_netto'] = usdc_netto_progressivo
    df['patrimonio'] = df['btc_netto'] * prezzo_btc_attuale + df['usdc_netto']

    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['patrimonio'], marker='o', linestyle='-', color='blue')
    plt.title("Andamento del patrimonio totale (interesse composto)")
    plt.xlabel("Data")
    plt.ylabel("Valore stimato in USDC")
    plt.grid(True)
    st.pyplot(plt)

def main():
    st.sidebar.header("Impostazioni")
    prezzo_btc_attuale = st.sidebar.number_input("Prezzo BTC attuale (USDC)", value=28000.0, step=100.0)

    st.write(f"### Prezzo BTC attuale impostato: {prezzo_btc_attuale:.2f} USDC")

    df_registro = carica_dati_registro()
    if df_registro.empty:
        st.warning("Nessun dato trovato nel foglio Registro.")
        return

    st.write("### Ultime operazioni")
    st.dataframe(df_registro.sort_values('timestamp', ascending=False).head(15))

    btc, usdc, patrimonio = calcola_patrimonio(df_registro, prezzo_btc_attuale)
    profitto_totale = df_registro['profitto'].sum()

    st.write(f"**BTC netto posseduto:** {btc:.6f} BTC")
    st.write(f"**USDC netto disponibile:** {usdc:.2f} USDC")
    st.write(f"**Profitto netto totale:** {profitto_totale:.2f} USDC")
    st.write(f"**Patrimonio totale stimato:** {patrimonio:.2f} USDC")

    grafico_interesse_composto(df_registro, prezzo_btc_attuale)

if __name__ == "__main__":
    main()
