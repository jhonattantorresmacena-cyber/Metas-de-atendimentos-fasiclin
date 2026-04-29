import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da Página (Deve ser a primeira coisa do Streamlit)
st.set_page_config(page_title="FASICLIN - Dashboard", layout="wide")

# 2. URL do seu Google Sheets (CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHp4J9odCsZapd1bUFHsJYrE7jQGH8VUoyEfb4sVM7py71J3XPJ7dmjKymMrQ3pQ/pub?output=csv"

# 3. Função de Carregamento com Limpeza de Dados
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # Limpeza de nomes de colunas (remove quebras de linha e espaços extras)
        df.columns = [
            str(col).replace('\n', ' ').replace('\r', ' ').strip().upper() 
            for col in df.columns
        ]
        # Remove espaços duplos internos
        df.columns = [" ".join(col.split()) for col in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return pd.DataFrame()

# 4. Processamento de Dados
df_raw = load_data()

if not df_raw.empty:
    # Mapeamento inteligente de colunas
    def encontrar_coluna(lista_colunas, palavras_chave):
        for col in lista_colunas:
            if all(palavra in col for palavra in palavras_chave):
                return col
        return None

    # Busca as colunas principais
    COL_META = encontrar_coluna(df_raw.columns, ["QUANTIDE", "SEMESTRE"]) or \
               encontrar_coluna(df_raw.columns, ["QUANTIDADE", "SEMESTRE"])
    
    COL_CLINICA = "CLINICA"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL"]

    # Validação de segurança
    if not COL_META:
        st.error(f"Coluna de Meta não encontrada. Colunas detectadas: {list(df_raw.columns)}")
        st.stop()

    # Conversão de valores para números (garante que cálculos funcionem)
    for c in [COL_META] + MESES:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # --- INTERFACE DO DASHBOARD ---
    st.title("🏥 FASICLIN - Dashboard de Produtividade")
    st.markdown("---")

    # Filtros
    col_u, col_c = st.columns(2)
    with col_u:
        unidade = st.selectbox("Unidade", ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"])
    with col_c:
        clinicas = ["TODAS"] + sorted(df_raw[COL_CLINICA].unique().tolist())
        clinica_sel = st.selectbox("Filtrar Clínica", clinicas)

    # Lógica de Filtro
    df_filtered = df_raw.copy()
    if clinica_sel != "TODAS":
        df_filtered = df_filtered[df_filtered[COL_CLINICA] == clinica_sel]

    # Cálculos Totais
    total_meta = df_filtered[COL_META].sum()
    total_realizado = df_filtered[MESES].sum().sum()
    percentual = (total_realizado / total_meta * 100) if total_meta > 0 else 0
    falta = max(0, total_meta - total_realizado)

    # Alerta de Metas
    if falta > 0:
        st.info(f"**Acompanhamento:** Faltam **{falta:.0f}** procedimentos. Média necessária: **{falta/4:.0f}/mês**.")
    else:
        st.success("🎉 Meta atingida para esta seleção!")

    # Gráficos
    c1, c2 = st.columns([1, 2])
    
    with c1:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=[total_realizado, falta],
            hole=.7,
            marker_colors=['#299947', '#f2f2f2'],
            textinfo='none'
        )])
        fig_donut.update_layout(
            title="Eficiência Total",
            annotations=[dict(text=f'{percentual:.0f}%', x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#004a87")],
            showlegend=False, height=350
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c2:
        # Agrupamento para o gráfico de barras
        df_bar = df_filtered.groupby(COL_CLINICA).agg({COL_META: 'sum'}).reset_index()
        df_bar['REALIZADO'] = df_filtered.groupby(COL_CLINICA)[MESES].sum().sum(axis=1).values
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=df_bar[COL_CLINICA], y=df_bar['REALIZADO'], marker_color='#299947'))
