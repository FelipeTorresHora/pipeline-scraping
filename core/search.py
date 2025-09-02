# core/search.py

from ddgs import DDGS
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==== Configurações da Busca ====
# Reduzido para uma experiência mais rápida no Streamlit
NUM_THREADS = 5       # Mais threads para ser mais rápido na web
TEMPO_ESPERA = 1      # Espera curta entre buscas para não sobrecarregar
MAX_RESULTS_PER_SEARCH = 3 # Focar nos primeiros resultados que são mais relevantes
# =================================

def buscar_instagram_perfil(termo_busca: str):
    """
    Executa a busca no DuckDuckGo e retorna o primeiro resultado de Instagram encontrado.
    Retorna apenas a URL para simplificar.
    """
    try:
        with DDGS(timeout=10) as ddgs:
            # Iteramos pelos resultados e paramos no primeiro link do Instagram
            for resultado in ddgs.text(termo_busca, max_results=MAX_RESULTS_PER_SEARCH):
                url = resultado.get("href", "")
                if "instagram.com" in url:
                    # Limpa a URL para pegar apenas o perfil principal
                    clean_url = url.split("?")[0]
                    if clean_url.endswith('/'):
                        clean_url = clean_url[:-1]
                    return clean_url
        return None  # Retorna None se nenhum perfil for encontrado
    except Exception as e:
        print(f"❌ Erro durante a busca '{termo_busca}': {e}")
        return None


def processar_empresa(cnpj: str, razao_social: str, municipio: str):
    """
    Prepara o termo de busca para uma empresa e executa a busca.
    Retorna um dicionário com o resultado.
    """
    # Evita buscas inúteis se não houver dados essenciais
    if not razao_social or not municipio:
        return {
            "cnpj_basico": cnpj,
            "razao_social": razao_social,
            "municipio": municipio,
            "instagram_url": "Dados insuficientes para busca"
        }

    # Monta um termo de busca eficaz
    termo = f'"{razao_social}" {municipio} instagram'
    
    # Adiciona uma pequena pausa para não sobrecarregar a API de busca
    time.sleep(TEMPO_ESPERA)
    
    url_encontrada = buscar_instagram_perfil(termo)
    
    return {
        "cnpj_basico": cnpj,
        "razao_social": razao_social,
        "municipio": municipio,
        "instagram_url": url_encontrada if url_encontrada else "Não encontrado"
    }

def buscar_em_lote(empresas_df):
    """
    Usa ThreadPoolExecutor para processar uma lista de empresas em paralelo.
    """
    resultados = []
    total_empresas = len(empresas_df)
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Cria uma lista de "tarefas" para o executor
        futures = [
            executor.submit(
                processar_empresa,
                row["cnpj_basico"],
                row["razao_social"],
                row["municipio"] # Assumimos que a coluna 'municipio' contém o nome da cidade
            )
            for index, row in empresas_df.iterrows()
        ]
        
        # Coleta os resultados à medida que ficam prontos
        for future in as_completed(futures):
            try:
                resultados.append(future.result())
            except Exception as e:
                print(f"❌ Erro ao processar uma empresa: {e}")
                
    return resultados