@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Limpeza radical: remove quebras de linha (\n, \r), espaços duplos e coloca em maiúsculo
        df.columns = [
            str(col).replace('\n', ' ').replace('\r', ' ').strip().upper() 
            for col in df.columns
        ]
        # Remove espaços duplos que podem surgir após tirar o \n
        df.columns = [" ".join(col.split()) for col in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- MAPEAMENTO AUTOMÁTICO DE COLUNAS ---
    # Em vez de nome fixo, buscamos por palavras que existem na coluna
    def encontrar_coluna(lista_colunas, palavras_chave):
        for col in lista_colunas:
            if all(palavra in col for palavra in palavras_chave):
                return col
        return None

    # Busca a coluna de meta (ex: que tenha QUANTIDADE e SEMESTRE)
    COL_META = encontrar_coluna(df_raw.columns, ["QUANTIDADE", "SEMESTRE"])
    COL_CLINICA = "CLINICA"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL"]

    # Se não encontrar pelo nome 'bonito', tenta o nome com erro que apareceu no print
    if not COL_META:
        if "QUANTIDE DE PROCEDIMENTO POR SEMESTRE" in df_raw.columns:
            COL_META = "QUANTIDE DE PROCEDIMENTO POR SEMESTRE"
        else:
            st.error(f"Não encontrei a coluna de Meta. Colunas lidas: {list(df_raw.columns)}")
            st.stop()

    # Conversão garantida para números
    for c in [COL_META] + MESES:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)
