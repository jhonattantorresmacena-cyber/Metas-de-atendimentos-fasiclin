import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium v2.3", layout="wide")

# Estilização CSS para manter a identidade visual original
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    div[data-testid="stMetricValue"] { color: #004a87; }
    </style>
    """, unsafe_allow_html=True)

# URL do CSV (Google Sheets publicado)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHp4J9odCsZapd1bUFHsJYrE7jQGH8VUoyEfb4sVM7py71J3XPJ7dmjKymMrQ3pQ/pub?output=csv"

@st.cache_data(ttl=600) # Atualiza o cache a cada 10 minutos
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Normalização de colunas similar ao código JS original
        df.columns = [col.strip().upper() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregamento dos dados
df_raw = load_data()

if not df_raw.empty:
    # Header
    st.title("🏥 FASICLIN - Dashboard de Produtividade")
    st.subheader("Acompanhamento de Metas e Procedimentos")
    st.divider()

    # Controles (Sidebar ou Topo)
    col_unidade, col_clinica = st.columns(2)
    
    with col_unidade:
        # No original as unidades eram abas da planilha, aqui assumimos uma coluna 'UNIDADE' 
        # ou filtramos conforme a estrutura dos dados
        unidades = ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"]
        unidade_selected = st.selectbox("Selecione a Unidade", unidades)

    # Filtragem por Clínica (Dinâmica baseada nos dados)
    clinicas_disponiveis = ["TODAS"] + sorted(df_raw["CLINICA"].unique().tolist())
    with col_clinica:
        clinica_selected = st.selectbox("Filtrar Clínica", clinicas_disponiveis)

    # Lógica de Filtro
    df_filtered = df_raw.copy()
    if clinica_selected != "TODAS":
        df_filtered = df_filtered[df_filtered["CLINICA"] == clinica_selected]

    # Cálculos (Fevereiro + Março + Abril)
    # Ajuste os nomes das colunas conforme sua planilha real
    col_meta = "QUANTIDADE DE PROCEDIMENTO POR SEMESTRE"
    meses_realizados = ["FEVEREIRO", "MARÇO", "ABRIL"]
    
    soma_meta = df_filtered[col_meta].sum()
    soma_realizado = df_filtered[meses_realizados].sum().sum()
    percentual = (soma_realizado / soma_meta * 100) if soma_meta > 0 else 0
    falta = max(0, soma_meta - soma_realizado)

    # Alerta de Metas
    if falta > 0:
        st.info(f"🚩 **Acompanhamento de Metas:** Faltam **{falta:.0f}** procedimentos. Média necessária: **{falta/4:.0f}/mês**.")
    else:
        st.success("🎉 **Meta atingida para esta seleção!**")

    # Dashboard Grid
    col_donut, col_bar = st.columns([1, 2])

    with col_donut:
        # Gráfico de Rosca (Eficiência)
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=[soma_realizado, falta],
            hole=.7,
            marker_colors=['#299947', '#f2f2f2'],
            textinfo='none'
        )])
        fig_donut.update_layout(
            title="Eficiência Total",
            annotations=[dict(text=f'{percentual:.0f}%', x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#004a87")],
            showlegend=False,
            height=350
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_bar:
        # Gráfico de Barras (Realizado vs Meta)
        # Agrupando por clínica para o gráfico
        df_chart = df_filtered.groupby("CLINICA").agg({
            col_meta: 'sum'
        }).reset_index()
        df_chart['REALIZADO'] = df_filtered.groupby("CLINICA")[meses_realizados].sum().sum(axis=1).values

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=df_chart['CLINICA'], y=df_chart['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=df_chart['CLINICA'], y=df_chart[col_meta], marker_color='#004a87'))
        
        fig_bar.update_layout(barmode='group', title="Realizado vs Meta por Clínica", height=350)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Detalhamento (Lista)
    st.markdown("### Detalhamento")
    
    # Criando os cards de detalhamento
    cols = st.columns(3)
    for i, (_, row) in enumerate(df_chart.iterrows()):
        perc_item = (row['REALIZADO'] / row[col_meta] * 100) if row[col_meta] > 0 else 0
        with cols[i % 3]:
            st.metric(
                label=row['CLINICA'], 
                value=f"{row['REALIZADO']:.0f}", 
                delta=f"{perc_item:.1f}% da Meta"
            )

else:
    st.warning("Aguardando conexão com a planilha ou planilha vazia.")
