import time
import unicodedata
from typing import Dict, List, Set, Tuple, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from ddgs import DDGS

NUM_THREADS = 4
TEMPO_ESPERA = 3
MAX_RESULTS_PER_SEARCH = 3
VALIDATION_THRESHOLD = 0.2


# ==================== Verficações com dados RFB ====================

def normalizar_texto(texto: Any) -> str:
    """Normaliza texto para comparação (remove acentos, converte para minúsculo)."""
    if pd.isna(texto):
        return ""
    
    texto = str(texto)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    
    return texto.lower().strip()

def extrair_palavras_chave(empresa_data: pd.Series) -> Set[str]:
    """Extrai um conjunto de palavras-chave relevantes de uma empresa para validação."""
    palavras = set()
    
    campos_texto = [
        'razao_social', 'nome_fantasia', 'logradouro', 'complemento','cnpj_basico',
        'bairro', 'correio_eletronico', 'telefone1','cep_limpo','municipio_nome'
    ]
    
    for campo in campos_texto:
        if campo in empresa_data and pd.notna(empresa_data[campo]):
            valor = empresa_data[campo]
            if valor and str(valor).strip():
                texto_normalizado = normalizar_texto(valor)
                # Adiciona palavras com 2 ou mais caracteres
                palavras_campo = {p for p in texto_normalizado.split() if len(p) >= 2}
                palavras.update(palavras_campo)
    
    # Remove palavras genéricas para melhorar a precisão
    palavras_comuns = {
        'ltda', 'cia', 'comercial', 'industria', 'servicos', 'eireli', 'me', 'sa',
        'empresa', 'rua', 'avenida', 'centro', 'bairro', 'com', 'br', 'gov'
    }
    
    return palavras - palavras_comuns

def verificar_correspondencia_descricao(
    palavras_chave_empresa: Set[str],
    descricao: str
) -> Tuple[bool, List[str]]:
    """
    Verifica se as palavras-chave da empresa aparecem na descrição do resultado da busca.
    Retorna um booleano para a correspondência e a lista de palavras encontradas.
    """
    if not palavras_chave_empresa or not descricao or pd.isna(descricao):
        return False, []
        
    descricao_norm = normalizar_texto(descricao)
    palavras_encontradas = [
        palavra for palavra in palavras_chave_empresa if palavra in descricao_norm
    ]
    
    if not palavras_encontradas:
        return False, []
    
    taxa_correspondencia = len(palavras_encontradas) / len(palavras_chave_empresa)
    tem_correspondencia = (taxa_correspondencia >= VALIDATION_THRESHOLD) or (len(palavras_encontradas) >= 2)
    
    return tem_correspondencia, palavras_encontradas


# ==================== Funções de Busca e Processamento ====================

def buscar_e_validar_perfil(
    termo_busca: str,
    palavras_chave_empresa: Set[str]
) -> Tuple[str | None, List[str]]:
    """
    Executa a busca e itera pelos resultados, validando cada um contra as palavras-chave.
    Retorna a URL do primeiro perfil validado e as palavras que confirmaram a validação.
    """
    try:
        with DDGS(timeout=10) as ddgs:
            for resultado in ddgs.text(termo_busca, max_results=MAX_RESULTS_PER_SEARCH):
                url = resultado.get("href", "")
                if "instagram.com" in url:
                    descricao = resultado.get("body", "") + " " + resultado.get("title", "")
                    
                    # Realiza a validação
                    tem_corresp, palavras_encontradas = verificar_correspondencia_descricao(
                        palavras_chave_empresa, descricao
                    )
                    
                    if tem_corresp:
                        # Limpa a URL para retornar apenas o perfil principal
                        clean_url = url.split("?")[0]
                        if clean_url.endswith('/'):
                            clean_url = clean_url[:-1]
                        return clean_url, palavras_encontradas
                        
        return None, []  # Nenhum perfil validado encontrado
    except Exception as e:
        print(f"❌ Erro durante a busca por '{termo_busca}': {e}")
        return None, []

def processar_empresa(empresa_dados: pd.Series) -> Dict[str, Any]:
    """
    Processa uma única empresa: extrai palavras-chave, busca e valida o perfil.
    Retorna um dicionário com o resultado detalhado.
    """
    # Extrai dados básicos do registro da empresa
    cnpj = empresa_dados.get('cnpj_basico', '')
    razao_social = empresa_dados.get('razao_social', '')
    municipio = empresa_dados.get('municipio', '')
    
    # Validação inicial dos dados
    if not razao_social or not municipio:
        return {
            "cnpj_basico": cnpj, "razao_social": razao_social, "municipio": municipio,
            "instagram_url": "Dados insuficientes", "status_validacao": "Falha",
            "palavras_encontradas": [], "palavras_chave_usadas": []
        }
    
    # 1. Cria o "DNA" da empresa para validação
    palavras_chave = extrair_palavras_chave(empresa_dados)
    
    # 2. Monta o termo de busca
    termo = f'"{razao_social}" {municipio} instagram'
    
    # Pequena pausa para evitar sobrecarga
    time.sleep(TEMPO_ESPERA)
    
    # 3. Busca e valida o perfil
    url_encontrada, palavras_match = buscar_e_validar_perfil(termo, palavras_chave)
    
    # 4. Monta o dicionário de resultado
    if url_encontrada:
        status = "Perfil Validado"
        url_final = url_encontrada
    else:
        status = "Nenhum perfil validado"
        url_final = "Não encontrado"
        
    return {
        "cnpj_basico": cnpj,
        "razao_social": razao_social,
        "municipio": municipio,
        "instagram_url": url_final,
        "status_validacao": status,
        "palavras_encontradas": ", ".join(palavras_match),
        "palavras_chave_usadas": ", ".join(sorted(list(palavras_chave)))
    }

def buscar_em_lote(empresas_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Usa ThreadPoolExecutor para processar uma lista de empresas em paralelo.
    """
    resultados = []
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Submete uma tarefa para cada linha (pd.Series) do DataFrame
        futures = [
            executor.submit(processar_empresa, row)
            for index, row in empresas_df.iterrows()
        ]
        
        # Coleta os resultados à medida que ficam prontos
        for future in as_completed(futures):
            try:
                resultados.append(future.result())
            except Exception as e:
                print(f"❌ Erro ao processar o resultado de uma thread: {e}")
                
    return resultados