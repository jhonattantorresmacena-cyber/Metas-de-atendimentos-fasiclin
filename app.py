import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuração visual da página
st.set_page_config(page_title="FASICLIN - Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { color: #004a87; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 FASICLIN - Dashboard de Produtividade")

# --- BARRA LATERAL ---
st.sidebar.header("Upload de Dados")
uploaded_file = st.sidebar.file_input("Anexe o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Carrega as abas (Unidades)
    xls = pd.ExcelFile(uploaded_file)
    unidade = st.sidebar.selectbox("Selecione a Unidade", xls.sheet_names)
    
    # Lendo os dados da aba selecionada
    df = pd.read_excel(uploaded_file, sheet_name=unidade)
    
    # Limpeza de nomes de colunas
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Identificando colunas de meses presentes (conforme seu HTML: FEV, MAR, ABR)
    meses_disponiveis = [c for c in ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO"] if c in df.columns]
    col_meta = "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"

    # Filtro de Clínica
    clinicas = ["TODAS"] + sorted(df["CLINICA"].dropna().unique().tolist())
    filtro_clinica = st.sidebar.selectbox("Filtrar por Clínica", clinicas)

    if filtro_clinica != "TODAS":
        df = df[df["CLINICA"] == filtro_clinica]

    # --- CÁLCULOS ---
    total_meta = df[col_meta].sum()
    total_realizado = df[meses_disponiveis].sum(axis=1).sum()
    percentual = (total_realizado / total_meta) * 100 if total_meta > 0 else 0
    falta = total_meta - total_realizado

    # --- MÉTRICAS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meta Total", f"{total_meta:,.0f}")
    c2.metric("Realizado", f"{total_realizado:,.0f}")
    c3.metric("Eficiência", f"{percentual:.1f}%")
    c4.metric("Saldo", f"{falta:,.0f}")

    st.divider()

    # --- GRÁFICOS ---
    col_esq, col_dir = st.columns([1, 2])

    with col_esq:
        st.write("### Eficiência Geral")
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=[total_realizado, max(0, falta)],
            hole=.7,
            marker_colors=['#299947', '#f2f2f2'],
            textinfo='none'
        )])
        fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        fig_donut.add_annotation(text=f"{percentual:.0f}%", x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#004a87")
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_dir:
        st.write("### Comparativo de Produção")
        # Agrupando por clínica para o gráfico de barras
        df_resumo = df.groupby("CLINICA").agg({col_meta: 'sum'}).reset_index()
        df_resumo['REALIZADO'] = df.groupby("CLINICA")[meses_disponiveis].sum().sum(axis=1).values
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=df_resumo['CLINICA'], y=df_resumo['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=df_resumo['CLINICA'], y=df_resumo[col_meta], marker_color='#004a87'))
        fig_bar.update_layout(barmode='group', height=350, margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.write("### Detalhamento por Procedimento")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Por favor, faça o upload do arquivo Excel na barra lateral para visualizar os dados.")
