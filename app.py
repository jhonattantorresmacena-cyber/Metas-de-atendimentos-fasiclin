import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# 2. Link Base da Planilha (Certifique-se que o ID está correto)
# O ID é a parte entre 'd/' e '/edit' na URL do seu navegador
SHEET_ID = "1THp4J9odCsZapd1bUFHsJYrE7jQGH8VUoyEfb4sVM7py71J3XPJ7dmjKymMrQ3pQ"

@st.cache_data(ttl=60)
def load_all_data():
    # Lista exata das abas - Verifique se não há espaços nos nomes das abas no Google
    abas = ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"]
    lista_dfs = []
    
    for aba in abas:
        try:
            # Formato de link para exportar aba específica como CSV
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={aba}"
            df_temp = pd.read_csv(url)
            
            # Limpeza de colunas
            df_temp.columns = [str(c).replace('\n', ' ').strip().upper() for c in df_temp.columns]
            df_temp['UNIDADE_ORIGEM'] = aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.warning(f"Não foi possível ler a aba: {aba}. Verifique se o nome está idêntico na planilha.")
            
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True)
    return pd.DataFrame()

df_raw = load_all_data()

# --- Restante do código de processamento e gráficos permanece igual ao anterior ---
if not df_raw.empty:
    st.success("Dados carregados com sucesso!")
    # ... (código dos gráficos aqui)
else:
    st.error("Erro crítico: Nenhuma aba pôde ser lida. Verifique o Compartilhamento da Planilha para 'Qualquer pessoa com o link'.")
