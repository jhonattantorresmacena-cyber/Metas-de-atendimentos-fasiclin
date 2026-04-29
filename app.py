import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# Estilização Customizada via CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Título e Logo
st.title("📊 FASICLIN - Gestão de Produtividade")
st.subheader("Controle de Metas e Procedimentos 2026")

# --- BARRA LATERAL (UPLOADER E FILTROS) ---
st.sidebar.header("Configurações")
uploaded_file = st.sidebar.file_input("Anexe o arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Carregar todas as abas para permitir seleção de Unidade
    xls = pd.ExcelFile(uploaded_file)
    unidade = st.sidebar.selectbox("Selecione a Unidade (Aba)", xls.sheet_names)
    
    # Processamento de Dados
    df = pd.read_excel(uploaded_file, sheet_name=unidade)
    
    # Limpeza básica (ajustar nomes de colunas para maiúsculas e sem espaços extras)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Filtro de Clínica
    todas_clinicas = ["TODAS"] + sorted(df["CLINICA"].unique().tolist())
    clinica_selecionada = st.sidebar.selectbox("Filtrar por Clínica", todas_clinicas)
    
    if clinica_selecionada != "TODAS":
        df = df[df["CLINICA"] == clinica_selecionada]

    # --- CÁLCULOS ---
    # Meses de realização (Ajuste conforme as colunas do seu Excel)
    meses_col = ["FEVEREIRO", "MARÇO", "ABRIL"] 
    meta_col = "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"

    total_meta = df[meta_col].sum()
    total_realizado = df[meses_col].sum(axis=1).sum()
    percentual = (total_realizado / total_meta) * 100 if total_meta > 0 else 0
    falta = total_meta - total_realizado

    # --- DASHBOARD LAYOUT ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Meta Semestral", f"{total_meta:,.0f}")
    col2.metric("Realizado Total", f"{total_realizado:,.0f}")
    col3.metric("Eficiência", f"{percentual:.1f}%")
    col4.metric("Saldo Restante", f"{falta:,.0f}", delta=-falta, delta_color="inverse")

    st.markdown("---")

    # --- GRÁFICOS ---
    g_col1, g_col2 = st.columns([1, 2])

    with g_col1:
        st.write("### Eficiência Total")
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=[total_realizado, max(0, falta)],
            hole=.7,
            marker_colors=['#299947', '#004a87']
        )])
        fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        fig_donut.add_annotation(text=f"{percentual:.0f}%", x=0.5, y=0.5, font_size=40, showarrow=False)
        st.plotly_chart(fig_donut, use_container_width=True)

    with g_col2:
        st.write("### Comparativo por Clínica")
        df_chart = df.copy()
        df_chart['REALIZADO'] = df[meses_col].sum(axis=1)
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=df_chart['CLINICA'], y=df_chart['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=df_chart['CLINICA'], y=df_chart[meta_col], marker_color='#004a87'))
        
        fig_bar.update_layout(barmode='group', margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABELA DE DETALHAMENTO ---
    st.write("### Detalhamento dos Dados")
    st.dataframe(df, use_container_width=True)

    # Alerta de Produtividade
    if falta > 0:
        media_necessaria = falta / 2 # Exemplo: Faltam Maio e Junho
        st.info(f"💡 **Atenção:** Faltam {falta:,.0f} procedimentos. Média necessária de {media_necessaria:,.0f}/mês para atingir a meta.")
    else:
        st.success("🎉 Parabéns! A meta da unidade/clínica selecionada foi atingida!")

else:
    st.info("Aguardando upload do arquivo Excel para gerar o dashboard.")
    st.image("https://img.icons8.com/clouds/200/000000/data-configuration.png")
