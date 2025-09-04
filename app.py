# app.py

import streamlit as st
import pandas as pd
import os
from core.search import buscar_em_lote

# --- Configuração da Página ---
st.set_page_config(
    page_title="Buscador de Instagram por CNAE",
    page_icon="🤖",
    layout="wide"
)

DATA_FILE_PATH = os.path.join("data", "tab_2_ceps.csv")
CNAE_DESCRIPTIONS_PATH = os.path.join("data", "codigos_cnae_2.csv")

SITUACAO_CADASTRAL_MAP = {
    "1": "Nula",
    "2": "Ativa",
    "3": "Suspensa",
    "4": "Inapta",
    "5": "Ativa Não Regular",
    "8": "Baixada",
}

# --- Funções Auxiliares ---

@st.cache_data
def carregar_dados_empresas(caminho_arquivo):
    """Carrega e processa o arquivo de empresas, tratando erros e validando estrutura."""
    if not os.path.exists(caminho_arquivo):
        st.error(f"Erro: Arquivo de dados não encontrado em '{caminho_arquivo}'.")
        return None
    try:
        df = pd.read_csv(caminho_arquivo, dtype=str)
        
        # Validação das colunas essenciais
        colunas_necessarias = ["cnpj_basico", "razao_social", "municipio", "cnae_fiscal_principal", "situacao_cadastral"]
        if not all(col in df.columns for col in colunas_necessarias):
            st.error(f"O arquivo de dados precisa conter as colunas: {', '.join(colunas_necessarias)}")
            return None
        
        # Cria a coluna com a descrição da situação cadastral
        df['situacao_cadastral_desc'] = df['situacao_cadastral'].map(SITUACAO_CADASTRAL_MAP).fillna("Desconhecida")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo de empresas: {e}")
        return None

@st.cache_data
def carregar_descricoes_cnae(caminho_arquivo):
    """Carrega o arquivo com as descrições dos CNAEs."""
    if not os.path.exists(caminho_arquivo):
        st.warning(f"Arquivo de descrições de CNAE não encontrado em '{caminho_arquivo}'. As descrições não serão exibidas.")
        return None
    try:
        df_cnae = pd.read_csv(caminho_arquivo, sep=';', dtype=str)
        df_cnae = df_cnae.rename(columns={'CNAE': 'codigo', 'DESCRIÇÃO': 'descricao'})
        return df_cnae
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de descrições de CNAE: {e}")
        return None

@st.cache_data
def convert_df_to_csv(df):
    """Converte um DataFrame para CSV em memória para download."""
    return df.to_csv(index=False).encode('utf-8')

# --- Interface do Usuário ---

st.title("🚀 Buscador de Instagram de Empresas por CNAE")
st.markdown("""
Esta ferramenta permite que você faça o upload de um arquivo CSV de empresas (como a amostra da Receita Federal), 
filtre por um ou mais códigos **CNAE Principal** e, em seguida, busque automaticamente o perfil do Instagram de cada empresa filtrada.
""")

# --- Passo 1: Upload do Arquivo ---
df_empresas = carregar_dados_empresas(DATA_FILE_PATH)
df_cnae_desc = carregar_descricoes_cnae(CNAE_DESCRIPTIONS_PATH)

if df_empresas is not None:
    st.header("1. Filtre as empresas por CNAE")
    
    cnae_options_display = ["Selecione uma atividade..."]
    cnae_code_map = {}
    
    if df_cnae_desc is not None:
        # Cruza os CNAEs existentes no arquivo de empresas com suas descrições
        cnaes_unicos = pd.DataFrame(df_empresas['cnae_fiscal_principal'].unique(), columns=['codigo'])
        cnaes_com_descricao = pd.merge(cnaes_unicos, df_cnae_desc, on='codigo', how='left').fillna('Descrição não encontrada')
        
        for _, row in cnaes_com_descricao.sort_values(by='codigo').iterrows():
            display_text = f"{row['codigo']} - {row['descricao']}"
            cnae_options_display.append(display_text)
            cnae_code_map[display_text] = row['codigo'] 
    else:
        # Fallback: Se o arquivo de descrição não existir, mostra apenas os códigos
        cnae_options_display.extend(sorted(df_empresas['cnae_fiscal_principal'].unique()))

    # Cria o selectbox com as opções enriquecidas
    selecao_formatada = st.selectbox(
        "Selecione a Atividade Econômica (CNAE) Principal",
        options=cnae_options_display
    )
    
    # Extrai o código CNAE da seleção do usuário
    cnae_selecionado = None
    if selecao_formatada != "Selecione uma atividade...":
        if df_cnae_desc is not None:
            cnae_selecionado = cnae_code_map.get(selecao_formatada)
        else:
            cnae_selecionado = selecao_formatada
            
    if cnae_selecionado:
        # Filtra o DataFrame com base no CNAE selecionado
        df_filtrado = df_empresas[df_empresas['cnae_fiscal_principal'] == cnae_selecionado].copy()
        
        st.write(f"Foram encontradas **{len(df_filtrado)}** empresas com o CNAE **{cnae_selecionado}**.")
        
        if not df_filtrado.empty:
            st.dataframe(df_filtrado[[
                'razao_social', 
                'nome_fantasia', 
                'municipio_nome', 
                'situacao_cadastral_desc' 
            ]].rename(columns={'situacao_cadastral_desc': 'Situação Cadastral'})) 
            
            st.header("2. Inicie a busca pelos perfis")
            if st.button("🔎 Buscar Perfis do Instagram", type="primary"):
                with st.spinner("Buscando e validando perfis... Isso pode levar alguns minutos."):
                    resultados = buscar_em_lote(df_filtrado)

                if resultados:
                    df_resultados = pd.DataFrame(resultados)
                    perfis_validados = len(df_resultados[df_resultados['status_validacao'] == 'Perfil Validado'])
                    st.success(f"Busca finalizada! Foram encontrados e validados {perfis_validados} perfis de Instagram.")
                    
                    st.dataframe(df_resultados)
                    
                    st.header("3. Exporte os resultados")
                    csv_export = convert_df_to_csv(df_resultados)
                    
                    st.download_button(
                        label="📥 Baixar resultados em CSV",
                        data=csv_export,
                        file_name=f"instagram_resultados_cnae_{cnae_selecionado}.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("Nenhum resultado foi retornado pela busca.")
else:
    st.info("A aplicação não pôde ser iniciada. Verifique os arquivos de dados na pasta 'data/'.")