import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="FASICLIN Dashboard - Google Sheets", layout="wide")

# Estilização CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #004a87; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 FASICLIN - Dashboard Tempo Real")
st.info("Conectado diretamente ao Google Sheets")

# --- FUNÇÃO PARA PUXAR DADOS DO GOOGLE SHEETS ---
def load_data():
    # ID da sua planilha extraído do link que você enviou
    sheet_id = "1yoPVCN4NRVC1ytEEuG5Tqb30ZGjiLHLG"
    # GID da aba específica (extraído do seu link #gid=1205707816)
    gid = "1205707816"
    
    # URL de exportação para CSV
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(url)
    return df

try:
    # Carregando os dados
    df_raw = load_data()
    
    # Limpeza de nomes de colunas (Maiúsculas e sem espaços)
    df = df_raw.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Mapeamento de colunas
    col_meta = "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"
    col_clinica = "CLINICA"
    # Meses que estão na sua planilha
    meses_disponiveis = [c for c in ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO"] if c in df.columns]

    # --- BARRA LATERAL ---
    st.sidebar.header("Filtros do Dashboard")
    
    if col_clinica in df.columns:
        clinicas = ["TODAS"] + sorted(df[col_clinica].dropna().unique().tolist())
        filtro = st.sidebar.selectbox("Selecione a Clínica", clinicas)
        if filtro != "TODAS":
            df = df[df[col_clinica] == filtro]

    # --- CÁLCULOS ---
    total_meta = pd.to_numeric(df[col_meta], errors='coerce').sum()
    total_realizado = df[meses_disponiveis].apply(pd.to_numeric, errors='coerce').sum().sum()
    
    percentual = (total_realizado / total_meta * 100) if total_meta > 0 else 0
    falta = total_meta - total_realizado

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta do Semestre", f"{total_meta:,.0f}")
    m2.metric("Realizado Acumulado", f"{total_realizado:,.0f}")
    m3.metric("Eficiência Atual", f"{percentual:.1f}%")
    m4.metric("Saldo Restante", f"{max(0, falta):,.0f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_esq, col_dir = st.columns([1, 2])

    with col_esq:
        st.subheader("Progresso Geral")
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
        st.subheader("Performance por Clínica")
        if col_clinica in df.columns:
            resumo = df.groupby(col_clinica).agg({col_meta: 'sum'}).reset_index()
            resumo['REALIZADO'] = df.groupby(col_clinica)[meses_disponiveis].sum().sum(axis=1).values
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name='Realizado', x=resumo[col_clinica], y=resumo['REALIZADO'], marker_color='#299947'))
            fig_bar.add_trace(go.Bar(name='Meta', x=resumo[col_clinica], y=resumo[col_meta], marker_color='#004a87'))
            fig_bar.update_layout(barmode='group', height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

    # Botão para atualizar dados manualmente
    if st.button("🔄 Atualizar Dados do Google Sheets"):
        st.rerun()

    with st.expander("Visualizar Base de Dados Completa"):
        st.dataframe(df_raw)

except Exception as e:
    st.error(f"Erro ao conectar com o Google Sheets: {e}")
    st.info("Certifique-se de que a planilha está configurada como 'Qualquer pessoa com o link pode ler'.")
