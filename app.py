import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="FASICLIN Dashboard", layout="wide")

# Estilização CSS para manter o padrão da marca
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #004a87; font-weight: bold; }
    .stAlert { border-left: 6px solid #004a87; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 FASICLIN - Dashboard de Produtividade")
st.markdown("---")

# --- BARRA LATERAL ---
st.sidebar.header("Upload de Dados")

# O COMANDO CORRETO É file_uploader
uploaded_file = st.sidebar.file_uploader("Anexe o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Carregar o Excel
        xls = pd.ExcelFile(uploaded_file)
        
        # Seleção de Unidade (Abas do Excel)
        unidade = st.sidebar.selectbox("Selecione a Unidade", xls.sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=unidade)
        
        # Normalizar nomes das colunas (Remover acentos e espaços extras)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Mapeamento de colunas conforme seu HTML/Excel
        col_meta = "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"
        meses_disponiveis = [c for c in ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO"] if c in df.columns]

        # Filtro de Clínica
        if "CLINICA" in df.columns:
            clinicas = ["TODAS"] + sorted(df["CLINICA"].dropna().unique().tolist())
            filtro = st.sidebar.selectbox("Filtrar por Clínica", clinicas)
            if filtro != "TODAS":
                df = df[df["CLINICA"] == filtro]

        # --- CÁLCULOS ---
        total_meta = df[col_meta].sum()
        total_realizado = df[meses_disponiveis].sum(axis=1).sum()
        percentual = (total_realizado / total_meta * 100) if total_meta > 0 else 0
        falta = total_meta - total_realizado

        # --- EXIBIÇÃO DE MÉTRICAS ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Meta Semestral", f"{total_meta:,.0f}")
        c2.metric("Realizado Atual", f"{total_realizado:,.0f}")
        c3.metric("Eficiência", f"{percentual:.1f}%")
        c4.metric("Saldo Restante", f"{max(0, falta):,.0f}")

        st.markdown("---")

        # --- GRÁFICOS ---
        col_esq, col_dir = st.columns([1, 2])

        with col_esq:
            st.subheader("Eficiência Geral")
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
            st.subheader("Produção por Clínica")
            if "CLINICA" in df.columns:
                # Agrupando para o gráfico de barras
                df_resumo = df.groupby("CLINICA").agg({col_meta: 'sum'}).reset_index()
                df_resumo['REALIZADO'] = df.groupby("CLINICA")[meses_disponiveis].sum().sum(axis=1).values
                
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(name='Realizado', x=df_resumo['CLINICA'], y=df_resumo['REALIZADO'], marker_color='#299947'))
                fig_bar.add_trace(go.Bar(name='Meta', x=df_resumo['CLINICA'], y=df_resumo[col_meta], marker_color='#004a87'))
                fig_bar.update_layout(barmode='group', height=350)
                st.plotly_chart(fig_bar, use_container_width=True)

        # Alerta de meta
        if falta > 0:
            st.info(f"💡 **Acompanhamento:** Faltam {falta:,.0f} atendimentos para a meta do semestre.")
        else:
            st.success("🎉 Parabéns! A meta foi atingida!")

    except Exception as e:
        st.error(f"Erro ao ler os dados: {e}")
        st.info("Verifique se as colunas 'CLINICA' e 'QUANTIDE DE PROCEDIMENTO POR SEMESTRE' estão presentes.")

else:
    st.info("👋 Bem-vindo! Carregue sua planilha Excel na barra lateral esquerda para visualizar os indicadores.")
