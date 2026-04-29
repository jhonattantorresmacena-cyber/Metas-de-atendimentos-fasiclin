import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard", layout="wide")

# URL do seu CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHp4J9odCsZapd1bUFHsJYrE7jQGH8VUoyEfb4sVM7py71J3XPJ7dmjKymMrQ3pQ/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # --- TRATAMENTO CRÍTICO DE COLUNAS ---
        # Remove espaços no início/fim e transforma tudo em MAIÚSCULO
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # Garante que as colunas numéricas sejam tratadas como números (remove erros de texto)
        cols_numericas = ["FEVEREIRO", "MARÇO", "ABRIL", "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"]
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return pd.DataFrame()

df_raw = load_data()

# Verificação de segurança: Mostrar colunas se der erro de novo
if not df_raw.empty:
    # 1. Definimos os nomes das colunas exatamente como o script vai buscar
    COL_CLINICA = "CLINICA"
    COL_META = "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL"]

    # 2. Verificamos se a coluna de Meta existe antes de calcular
    if COL_META not in df_raw.columns:
        st.error(f"Coluna '{COL_META}' não encontrada. Colunas disponíveis: {list(df_raw.columns)}")
        st.stop()

    # --- O RESTANTE DO SEU CÓDIGO DE FILTRO ---
    st.title("🏥 FASICLIN - Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        unidade = st.selectbox("Selecione a Unidade", ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"])
    
    clinicas = ["TODAS"] + sorted(df_raw[COL_CLINICA].unique().tolist())
    with col2:
        clinica_sel = st.selectbox("Filtrar Clínica", clinicas)

    # Filtragem
    df_filtered = df_raw.copy()
    if clinica_sel != "TODAS":
        df_filtered = df_filtered[df_filtered[COL_CLINICA] == clinica_sel]

    # Cálculos
    soma_meta = df_filtered[COL_META].sum()
    soma_realizado = df_filtered[MESES].sum().sum()
    
    # Exibição (Exemplo simplificado)
    st.metric("Total Realizado", f"{soma_realizado:.0f}", f"Meta: {soma_meta:.0f}")
    
    # ... (Seus gráficos de donut e barra seguem aqui)
