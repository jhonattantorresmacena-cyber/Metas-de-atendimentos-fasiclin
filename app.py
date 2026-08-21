import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# Estilização para os cards de detalhamento
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. Identificação da Planilha e GIDs fornecidos
SHEET_ID = "1yoPVCN4NRVC1ytEEuG5Tqb30ZGjiLHLG"
ABAS_CONFIG = {
    "SINOP": "1205707816",
    "SORRISO": "1415012993",
    "CUIABA": "1565006717",
    "RONDONOPOLIS": "426551434",
    "PRIMAVERA": "1535754805",
}


@st.cache_data(ttl=60)
def load_all_data():
    lista_dfs = []
    cache_buster = int(time.time() // 60)

    for nome_aba, gid in ABAS_CONFIG.items():
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cb={cache_buster}"
            df_temp = pd.read_csv(url)

            # Limpeza de colunas
            df_temp.columns = [
                str(c).replace("\n", " ").replace("\r", " ").strip().upper()
                for c in df_temp.columns
            ]
            df_temp.columns = [" ".join(c.split()) for c in df_temp.columns]

            df_temp["UNIDADE_NOME"] = nome_aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Erro ao carregar a unidade {nome_aba}: {e}")

    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()


df_raw = load_all_data()

if not df_raw.empty:

    def buscar_col(lista, termos):
        for c in lista:
            if all(t in c for t in termos):
                return c
        return None

    COL_META = buscar_col(df_raw.columns, ["QUANTID", "SEMESTRE"])
    COL_CLINICA = "CLINICA"
    MESES = ["AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    meses_existentes = [m for m in MESES if m in df_raw.columns]

    # Garantir formato numérico
    for c in ([COL_META] + meses_existentes):
        if c and c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0)

    # --- INTERFACE ---
    st.title("🏥 FASICLIN - Dashboard de Produtividade")

    # Filtros
    col_u, col_c = st.columns(2)
    with col_u:
        unidades_opcoes = ["TODAS"] + list(ABAS_CONFIG.keys())
        unidade_sel = st.selectbox("Unidade", unidades_opcoes)

    df_filtrado = df_raw.copy()
    if unidade_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado["UNIDADE_NOME"] == unidade_sel]

    with col_c:
        clinicas_disponiveis = ["TODAS"] + sorted(
            df_filtrado[COL_CLINICA].dropna().unique().tolist()
        )
        clinica_sel = st.selectbox("Filtrar Clínica", clinicas_disponiveis)

    if clinica_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado[COL_CLINICA] == clinica_sel]

    # Cáĺculos
    total_meta = (
        df_filtrado[COL_META].sum()
        if COL_META and COL_META in df_filtrado
        else 0
    )
    total_realizado = (
        df_filtrado[meses_existentes].sum().sum() if meses_existentes else 0
    )
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0

    soma_por_mes = (
        df_filtrado[meses_existentes].sum()
        if meses_existentes
        else pd.Series()
    )
    meses_com_dados = sum(soma_por_mes > 0)
    total_meses_periodo = len(meses_existentes)
    meses_restantes = max(1, total_meses_periodo - meses_com_dados)

    media_necessaria_mes = int(falta / meses_restantes) if falta > 0 else 0

    if falta > 0:
        st.info(
            f"**Acompanhamento de Metas:** Faltam **{falta:.0f}** procedimentos para atingir a meta total. "
            f"Considerando os meses restantes ({meses_restantes}), a média necessária é de **{media_necessaria_mes}** procedimentos/mês."
        )
    else:
        st.success(
            f"🎉 **Parabéns!** A meta de {total_meta:.0f} atendimentos foi atingida ou superada! (Realizado: {total_realizado:.0f})"
        )

    # Gráficos
    c_donut, c_bar = st.columns([1, 2])

    with c_donut:
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=["Realizado", "Pendente"],
                    values=[total_realizado, falta],
                    hole=0.8,
                    marker_colors=[
                        "#299947" if perc_total >= 100 else "#004a87",
                        "#f2f2f2",
                    ],
                    textinfo="none",
                )
            ]
        )
        fig_donut.update_layout(
            annotations=[
                dict(
                    text=f"Eficiência Total<br><b>{perc_total:.0f}%</b>",
                    x=0.5,
                    y=0.5,
                    font_size=20,
                    showarrow=False,
                )
            ],
            showlegend=False,
            height=350,
            margin=dict(t=0, b=0, l=0, r=0),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_bar:
        if COL_META and COL_META in df_filtrado.columns:
            resumo = (
                df_filtrado.groupby(COL_CLINICA)
                .agg({COL_META: "sum"})
                .reset_index()
            )
            resumo["REALIZADO"] = (
                df_filtrado.groupby(COL_CLINICA)[meses_existentes]
                .sum()
                .sum(axis=1)
                .values
            )

            fig_bar = go.Figure()
            fig_bar.add_trace(
                go.Bar(
                    name="Realizado",
                    x=resumo[COL_CLINICA],
                    y=resumo["REALIZADO"],
                    marker_color="#299947",
                )
            )
            fig_bar.add_trace(
                go.Bar(
                    name="Meta",
                    x=resumo[COL_CLINICA],
                    y=resumo[COL_META],
                    marker_color="#004a87",
                )
            )
            fig_bar.update_layout(
                barmode="group",
                height=350,
                margin=dict(t=20, b=20),
                legend=dict(orientation="h", y=11),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            resumo = pd.DataFrame()

    # Detalhamento
    if not resumo.empty:
        st.subheader("Detalhamento por Clínica")
        cols = st.columns(3)
        for i, (_, row) in enumerate(resumo.iterrows()):
            p_ind = (
                (row["REALIZADO"] / row[COL_META] * 100)
                if row[COL_META] > 0
                else 0
            )
            with cols[i % 3]:
                st.markdown(f"**{row[COL_CLINICA]}**")
                st.metric(
                    label="Realizado",
                    value=int(row["REALIZADO"]),
                    delta=f"{p_ind:.1f}% da meta",
                )
                st.progress(min(p_ind / 100, 1.0))
                st.caption(f"Meta: {int(row[COL_META])}")
                st.markdown("---")

   # Tabela de Dados Consolidados
    st.subheader("💾 Dados Consolidados")
    df_filtrado["TOTAL_REALIZADO_LINHA"] = df_filtrado[meses_existentes].sum(
        axis=1
    )

    # Definição na ordem solicitada: Unidade, Clínica, Meses, Total Realizado e Meta Por Semestre
    colunas_desejadas = (
        ["UNIDADE_NOME", COL_CLINICA]
        + meses_existentes
        + ["TOTAL_REALIZADO_LINHA"]
        + ([COL_META] if COL_META else [])
    )

    # Mantém apenas as colunas que realmente existem no DataFrame
    cols_presentes = [c for c in colunas_desejadas if c in df_filtrado.columns]

    df_exibicao = df_filtrado[cols_presentes].copy()
    st.dataframe(df_exibicao, use_container_width=True)

    csv_excel = df_exibicao.to_csv(
        index=False, sep=";", encoding="utf-8-sig"
    ).encode("utf-8-sig")
    st.download_button(
        label="📊 Baixar Tabela para Excel (.csv)",
        data=csv_excel,
        file_name=f"FASICLIN_{unidade_sel}.csv",
        mime="text/csv",
    )
