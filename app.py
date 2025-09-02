# app.py

import streamlit as st
import pandas as pd
import io
from core.search import buscar_em_lote

# --- Configuração da Página ---
st.set_page_config(
    page_title="Buscador de Instagram por CNAE",
    page_icon="🤖",
    layout="wide"
)

# --- Funções Auxiliares ---

@st.cache_data
def carregar_dados(arquivo):
    """Carrega e processa o arquivo CSV, tratando possíveis erros."""
    try:
        # Lê o arquivo CSV. O separador é inferido, mas pode ser especificado se necessário.
        df = pd.read_csv(arquivo)
        
        # Limpeza básica: remove espaços em branco das colunas de texto
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
            
        # Converte colunas importantes para o tipo correto para evitar erros
        df['cnpj_basico'] = df['cnpj_basico'].astype(str)
        df['cnae_fiscal_principal'] = df['cnae_fiscal_principal'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
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
st.header("1. Carregue seu arquivo de dados")
uploaded_file = st.file_uploader(
    "Escolha um arquivo CSV (use o `tab_2.csv` da pasta `data/` como exemplo)",
    type=["csv", "txt"]
)

if uploaded_file is not None:
    df = carregar_dados(uploaded_file)
    
    if df is not None:
        st.success(f"Arquivo carregado com sucesso! Encontradas {len(df)} empresas.")
        
        # Validação das colunas necessárias
        colunas_necessarias = ["cnpj_basico", "razao_social", "municipio", "cnae_fiscal_principal"]
        if not all(col in df.columns for col in colunas_necessarias):
            st.error(f"O arquivo precisa conter as seguintes colunas: {', '.join(colunas_necessarias)}")
        else:
            # --- Passo 2: Filtro por CNAE ---
            st.header("2. Filtre as empresas por CNAE")
            
            # Pega os CNAEs únicos e os ordena
            cnaes_unicos = sorted(df['cnae_fiscal_principal'].unique())
            
            cnae_selecionado = st.selectbox(
                "Digite ou selecione o CNAE Fiscal Principal",
                options=cnaes_unicos,
                index=None,
                placeholder="Selecione o CNAE desejado..."
            )
            
            if cnae_selecionado:
                # Filtra o DataFrame com base no CNAE selecionado
                df_filtrado = df[df['cnae_fiscal_principal'] == cnae_selecionado].copy()
                st.write(f"Foram encontradas **{len(df_filtrado)}** empresas com o CNAE **{cnae_selecionado}**.")
                
                if not df_filtrado.empty:
                    st.dataframe(df_filtrado)
                    
                    # --- Passo 3: Iniciar a Busca ---
                    st.header("3. Inicie a busca pelos perfis")
                    if st.button("🔎 Buscar Perfis do Instagram", type="primary"):
                        
                        with st.spinner("Buscando perfis... Isso pode levar alguns minutos, dependendo do número de empresas."):
                            # Barra de progresso para feedback visual
                            progress_bar = st.progress(0, text="Iniciando busca...")
                            
                            # Executa a busca em lote
                            resultados = buscar_em_lote(df_filtrado)
                            
                            progress_bar.progress(1.0, text="Busca concluída!")

                        if resultados:
                            df_resultados = pd.DataFrame(resultados)
                            
                            st.success(f"Busca finalizada! Foram encontrados {len(df_resultados[df_resultados['instagram_url'] != 'Não encontrado'])} perfis de Instagram.")
                            
                            # Exibe os resultados
                            st.dataframe(df_resultados)
                            
                            # --- Passo 4: Exportar Resultados ---
                            st.header("4. Exporte os resultados")
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
    st.info("Aguardando o upload de um arquivo CSV para começar.")