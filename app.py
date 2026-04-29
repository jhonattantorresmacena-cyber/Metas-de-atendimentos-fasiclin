import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="FASICLIN Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #004a87; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 FASICLIN - Dashboard Tempo Real")

@st.cache_data(ttl=600) # Atualiza o cache a cada 10 minutos
def load_data():
    sheet_id = "1yoPVCN4NRVC1ytEEuG5Tqb30ZGjiLHLG"
    gid = "1205707816"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(url)
    
    # Limpeza profunda dos nomes das colunas
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    # --- IDENTIFICAÇÃO DINÂMICA DE COLUNAS ---
    # Busca por colunas que contenham "QUANTIDADE" ou "META" e os meses
    col_meta = next((c for c in df.columns if "QUANT" in c or "META" in c), None)
    meses_disponiveis = [c for c in ["FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO"] if c in df.columns]
    col_clinica = "CLINICA" if "CLINICA" in df.columns else df.columns[0]

    if not col_meta:
        st.error("Não foi possível encontrar a coluna de Meta (Quantidade). Verifique o nome na planilha.")
        st.stop()

    # --- BARRA LATERAL ---
    st.sidebar.header("Filtros")
    clinicas = ["TODAS"] + sorted(df[col_clinica].dropna().unique().tolist())
    filtro = st.sidebar.selectbox("Selecione a Clínica", clinicas)
    
    if filtro != "TODAS":
        df = df[df[col_clinica] == filtro]

    # --- CÁLCULOS ---
    # Converte para numérico garantindo que erros virem 0
    total_meta = pd.to_numeric(df[col_meta], errors='coerce').sum()
    total_realizado = df[meses_disponiveis].apply(pd.to_numeric, errors='coerce').sum().sum()
    
    percentual = (total_realizado / total_meta * 100) if total_meta > 0 else 0
    falta = total_meta - total_realizado

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Total", f"{total_meta:,.0f}")
    m2.metric("Realizado", f"{total_realizado:,.0f}")
    m3.metric("Eficiência", f"{percentual:.1f}%")
    m4.metric("Saldo", f"{max(0, falta):,.0f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_esq, col_dir = st.columns([1, 2])

    with col_esq:
        st.subheader("Progresso")
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=[total_realizado, max(0, falta)],
            hole=.7,
            marker_colors=['#299947', '#f2f2f2'],
            textinfo='none'
        )])
        fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        fig_donut.add_annotation(text=f"{percentual:.0f}%", x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#004a87")
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_dir:
        st.subheader("Por Clínica")
        resumo = df.groupby(col_clinica).agg({col_meta: 'sum'}).reset_index()
        resumo['REALIZADO'] = df.groupby(col_clinica)[meses_disponiveis].sum().sum(axis=1).values
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=resumo[col_clinica], y=resumo['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=resumo[col_clinica], y=resumo[col_meta], marker_color='#004a87'))
        fig_bar.update_layout(barmode='group', height=350)
        st.plotly_chart(fig_bar, use_container_width=True)

    if st.button("🔄 Forçar Atualização de Dados"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Erro crítico: {e}")
