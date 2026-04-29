import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# 2. Link da sua planilha (ajustado para exportação de abas)
# Substitua o ID abaixo pelo ID da sua planilha se necessário
SHEET_ID = "1THp4J9odCsZapd1bUFHsJYrE7jQGH8VUoyEfb4sVM7py71J3XPJ7dmjKymMrQ3pQ"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

@st.cache_data(ttl=60)
def load_all_data():
    abas = ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"]
    lista_dfs = []
    
    for aba in abas:
        try:
            url = BASE_URL + aba
            df_temp = pd.read_csv(url)
            # Normaliza colunas
            df_temp.columns = [str(c).replace('\n', ' ').strip().upper() for c in df_temp.columns]
            df_temp['UNIDADE_ORIGEM'] = aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.warning(f"Não foi possível ler a aba: {aba}")
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

df_raw = load_all_data()

if not df_raw.empty:
    # --- MAPEAMENTO DE COLUNAS ---
    # Busca automática para evitar erro de 'QUANTIDE' ou 'QUANTIDADE'
    def buscar_col(lista, termos):
        for c in lista:
            if all(t in c for t in termos): return c
        return None

    COL_META = buscar_col(df_raw.columns, ["QUANTID", "SEMESTRE"])
    COL_CLINICA = "CLINICA"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL"]

    # Conversão Numérica
    for c in [COL_META] + MESES:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # --- INTERFACE ---
    st.title("🏥 FASICLIN - Dashboard de Produtividade")
    
    # Filtros
    c_un, c_cl = st.columns(2)
    with c_un:
        unidade_sel = st.selectbox("Selecione a Unidade", ["TODAS", "SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"])
    
    # Filtro de Unidade
    df_filtrado = df_raw.copy()
    if unidade_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado['UNIDADE_ORIGEM'] == unidade_sel]

    with c_cl:
        clinicas = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("Filtrar Clínica (Curso)", clinicas)

    if clinica_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS ---
    soma_meta = df_filtrado[COL_META].sum()
    soma_real = df_filtrado[MESES].sum().sum()
    perc_total = (soma_real / soma_meta * 100) if soma_meta > 0 else 0
    falta = max(0, soma_meta - soma_real)

    # Banner de Acompanhamento (Igual à imagem)
    st.info(f"**Acompanhamento de Metas:** Faltam **{falta:.0f}** procedimentos. Média necessária: **{falta/4:.0f}/mês**.")

    # --- GRÁFICOS (Correção do item 2) ---
    col_donut, col_bar = st.columns([1, 2])

    with col_donut:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Falta'],
            values=[soma_real, falta],
            hole=.7,
            marker_colors=['#299947', '#004a87'], # Verde e Azul Fasiclin
            textinfo='none'
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f'Eficiência Total<br><br><b>{perc_total:.0f}%</b>', x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=False, height=400, margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_bar:
        # Agrupa por clínica para o gráfico de barras
        resumo = df_filtrado.groupby(COL_CLINICA).agg({COL_META: 'sum'}).reset_index()
        resumo['REALIZADO'] = df_filtrado.groupby(COL_CLINICA)[MESES].sum().sum(axis=1).values
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=resumo[COL_CLINICA], y=resumo['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=resumo[COL_CLINICA], y=resumo[COL_META], marker_color='#004a87'))
        fig_bar.update_layout(barmode='group', height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- DETALHAMENTO POR CURSO (Igual à imagem) ---
    st.markdown("### Detalhamento")
    cols = st.columns(3)
    for i, (_, row) in enumerate(resumo.iterrows()):
        p_ind = (row['REALIZADO'] / row[COL_META] * 100) if row[COL_META] > 0 else 0
        with cols[i % 3]:
            st.write(f"**{row[COL_CLINICA]}**")
            st.caption(f"Meta: {row[COL_META]:.0f} | Realizado: {row['REALIZADO']:.0f}")
            st.progress(min(p_ind/100, 1.0))
            st.write(f"**{p_ind:.0f}%**")
            st.markdown("---")
else:
    st.error("Não foi possível carregar os dados. Verifique o compartilhamento da planilha.")
