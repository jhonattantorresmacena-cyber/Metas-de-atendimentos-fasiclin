import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide", page_icon="🏥")

# Estilização CSS Customizada
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #004a87;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Identificação da Planilha e GIDs
SHEET_ID = "1yoPVCN4NRVC1ytEEuG5Tqb30ZGjiLHLG"
ABAS_CONFIG = {
    "SINOP": "1205707816",
    "SORRISO": "1415012993",
    "CUIABA": "1565006717",
    "RONDONOPOLIS": "426551434",
    "PRIMAVERA": "1535754805"
}

@st.cache_data(ttl=60)
def load_all_data():
    lista_dfs = []
    cache_buster = int(time.time() // 60) 
    
    for nome_aba, gid in ABAS_CONFIG.items():
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cb={cache_buster}"
            df_temp = pd.read_csv(url)
            
            # Limpeza e padronização das colunas
            df_temp.columns = [
                str(c).replace('\n', ' ').replace('\r', ' ').strip().upper() 
                for c in df_temp.columns
            ]
            df_temp.columns = [" ".join(c.split()) for c in df_temp.columns]
            
            df_temp['UNIDADE_NOME'] = nome_aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Erro ao carregar a unidade {nome_aba}: {e}")
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

df_raw = load_all_data()

if not df_raw.empty:
    # Mapeamento de Colunas (Trata 'QUANTIDE' ou variações)
    def buscar_col(lista, termos):
        for c in lista:
            if all(t in c for t in termos): return c
        return None

    COL_META = buscar_col(df_raw.columns, ["QUANTID", "SEMESTRE"])
    COL_CLINICA = "CLINICA"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO"]

    # Garantir formato numérico
    for c in [COL_META] + MESES:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # --- INTERFACE ---
    st.title("🏥 FASICLIN - Dashboard de Produtividade")
    st.markdown("---")

    # Filtros (Adicionado "TODAS" na Unidade)
    col_u, col_c = st.columns(2)
    with col_u:
        unidades_disponiveis = ["TODAS"] + list(ABAS_CONFIG.keys())
        unidade_sel = st.selectbox("Filtrar Unidade", unidades_disponiveis)
    
    df_filtrado = df_raw.copy()
    if unidade_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado['UNIDADE_NOME'] == unidade_sel]

    with col_c:
        clinicas_disponiveis = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("Filtrar Clínica", clinicas_disponiveis)

    if clinica_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS DINÂMICOS ---
    total_meta = df_filtrado[COL_META].sum()
    total_realizado = df_filtrado[MESES].sum().sum()
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0

    # Lógica de Meses Ativos
    soma_por_mes = df_filtrado[MESES].sum()
    meses_com_dados = sum(soma_por_mes > 0)
    total_meses_periodo = len(MESES)
    meses_restantes = max(1, total_meses_periodo - meses_com_dados)

    media_necessaria_mes = int(falta / meses_restantes) if falta > 0 else 0

    # Banner de Acompanhamento
    if falta > 0:
        st.info(f"**Acompanhamento de Metas:** Faltam **{falta:.0f}** procedimentos para atingir a meta total. "
                f"Considerando os meses restantes ({meses_restantes}), a média necessária é de **{media_necessaria_mes}** procedimentos/mês.")
    else:
        st.success(f"🎉 **Parabéns!** A meta de {total_meta:.0f} atendimentos foi atingida ou superada! (Realizado: {total_realizado:.0f})")

    # --- GRÁFICOS ---
    c_donut, c_bar = st.columns([1, 2])

    with c_donut:
        # Se superou a meta, o gráfico mostra 100% preenchido para não quebrar o visual
        valores_donut = [total_realizado, falta] if falta > 0 else [100, 0]
        cor_donut = '#299947' if perc_total >= 100 else '#004a87'
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=valores_donut,
            hole=.75,
            marker_colors=[cor_donut, '#f2f2f2'],
            textinfo='none',
            sort=False
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f'Eficiência<br><b>{perc_total:.0f}%</b>', x=0.5, y=0.5, font_size=22, showarrow=False)],
            showlegend=False, height=320, margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_bar:
        # Agrupamento correto por clínica
        resumo = df_filtrado.groupby(COL_CLINICA).agg({COL_META: 'sum'}).reset_index()
        # Forma segura de somar os meses mantendo o alinhamento do index
        resumo['REALIZADO'] = df_filtrado.groupby(COL_CLINICA)[MESES].sum().sum(axis=1).values
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=resumo[COL_CLINICA], y=resumo['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=resumo[COL_CLINICA], y=resumo[COL_META], marker_color='#004a87'))
        fig_bar.update_layout(
            barmode='group', 
            height=320, 
            margin=dict(t=20, b=20), 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- DETALHAMENTO EM CARDS ---
    st.subheader("📊 Detalhamento por Clínica")
    
    # Grid dinâmico (3 colunas)
    cols = st.columns(3)
    for i, (_, row) in enumerate(resumo.iterrows()):
        p_ind = (row['REALIZADO'] / row[COL_META] * 100) if row[COL_META] > 0 else 0
        
        with cols[i % 3]:
            # Usando a classe CSS interna definida no início para ficar elegante
            st.markdown(f"""
            <div class="metric-card">
                <h4>{row[COL_CLINICA]}</h4>
                <p style="margin-bottom:2px;"><b>Realizado:</b> {int(row['REALIZADO'])}</p>
                <p style="margin-bottom:10px; color:#666;">Meta: {int(row[COL_META])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Barra de progresso logo abaixo do card correspondente
            st.progress(min(p_ind/100, 1.0))
            st.caption(f"**{p_ind:.1f}%** da meta atingida")
            st.markdown("<br>", unsafe_allow_html=True)
else:
    st.warning("Nenhum dado encontrado. Verifique se a planilha está compartilhada corretamente.")
