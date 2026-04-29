import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da página
st.set_page_config(page_title="FASICLIN Dashboard", layout="wide")

# 2. Função para transformar o link do Google Sheets em link de download CSV
def get_csv_url(url):
    # Extrai o ID da planilha e o GID da aba
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0]
        else:
            gid = "0"
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except:
        return None

# 3. Interface Principal
st.title("📊 FASICLIN - Dashboard de Produtividade")

# Link da sua planilha
url_planilha = "https://docs.google.com/spreadsheets/d/1yoPVCN4NRVC1ytEEuG5Tqb30ZGjiLHLG/edit?gid=1205707816#gid=1205707816"
csv_url = get_csv_url(url_planilha)

@st.cache_data(ttl=300) # Atualiza a cada 5 minutos
def load_data(url):
    df = pd.read_csv(url)
    # Limpa nomes de colunas: tira espaços, remove acentos e coloca em maiúsculas
    df.columns = df.columns.str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper()
    return df

try:
    df = load_data(csv_url)
    
    # Identificação flexível de colunas (para evitar o KeyError)
    # Procura colunas que contenham "QUANT" (Meta) e os meses
    col_meta = next((c for c in df.columns if "QUANT" in c or "META" in c), None)
    col_clinica = next((c for c in df.columns if "CLINICA" in c or "UNIDADE" in c), df.columns[0])
    
    meses = ["JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO"]
    meses_presentes = [c for c in df.columns if any(m in c for m in meses)]

    if col_meta is None:
        st.error(f"Coluna de Meta não encontrada. Colunas detectadas: {list(df.columns)}")
        st.stop()

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    clinicas = ["TODAS"] + sorted(df[col_clinica].dropna().unique().tolist())
    selecao = st.sidebar.selectbox("Selecione a Clínica", clinicas)

    if selecao != "TODAS":
        df = df[df[col_clinica] == selecao]

    # --- CÁLCULOS ---
    # Convertendo para número e tratando erros
    meta_total = pd.to_numeric(df[col_meta], errors='coerce').sum()
    realizado_total = df[meses_presentes].apply(pd.to_numeric, errors='coerce').sum().sum()
    
    percentual = (realizado_total / meta_total * 100) if meta_total > 0 else 0
    saldo = meta_total - realizado_total

    # --- DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meta Semestral", f"{meta_total:,.0f}")
    c2.metric("Realizado Total", f"{realizado_total:,.0f}")
    c3.metric("Eficiência", f"{percentual:.1f}%")
    c4.metric("Saldo Restante", f"{max(0, saldo):,.0f}")

    st.divider()

    col_g1, col_g2 = st.columns([1, 2])

    with col_g1:
        fig = go.Figure(data=[go.Pie(labels=['Realizado', 'Pendente'], 
                             values=[realizado_total, max(0, saldo)], 
                             hole=.7, marker_colors=['#299947', '#eeeeee'])])
        fig.update_layout(showlegend=False, title="Progresso da Meta")
        fig.add_annotation(text=f"{percentual:.0f}%", x=0.5, y=0.5, font_size=40, showarrow=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        resumo_bar = df.groupby(col_clinica).agg({col_meta: 'sum'}).reset_index()
        resumo_bar['REAL'] = df.groupby(col_clinica)[meses_presentes].sum().sum(axis=1).values
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=resumo_bar[col_clinica], y=resumo_bar['REAL'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=resumo_bar[col_clinica], y=resumo_bar[col_meta], marker_color='#004a87'))
        fig_bar.update_layout(barmode='group', title="Comparativo por Clínica")
        st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("Dados Brutos da Planilha"):
        st.write(df)

except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("💡 Verifique se a planilha do Google está compartilhada como 'Qualquer pessoa com o link pode ler'.")
