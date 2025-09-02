# Buscador de Instagram de Empresas por CNAE

Esta é uma aplicação web construída com Streamlit que permite buscar perfis do Instagram de empresas a partir de um arquivo CSV, filtrando por seu CNAE (Classificação Nacional de Atividades Econômicas).

## Funcionalidades

-   Upload de arquivos CSV/TXT contendo dados de empresas.
-   Filtro de empresas por código CNAE Fiscal Principal.
-   Busca automática no DuckDuckGo para encontrar o perfil do Instagram de cada empresa filtrada.
-   Exibição dos resultados em uma tabela interativa.
-   Download dos resultados em um novo arquivo CSV.

## Como Executar o Projeto

### 1. Pré-requisitos

-   Python 3.8 ou superior
-   Pip (gerenciador de pacotes do Python)

### 2. Clone o Repositório (Opcional)

Se você recebeu os arquivos em um ZIP, pode pular esta etapa.
```bash
git clone <url-do-seu-repositorio>
cd projeto_streamlit_cnae
```

### 3. Instale as Dependências

Navegue até a pasta do projeto no seu terminal e execute o seguinte comando para instalar todas as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

### 4. Execute a Aplicação

Ainda no terminal, na pasta raiz do projeto, execute o comando:

```bash
streamlit run app.py
```

Seu navegador abrirá automaticamente com a aplicação rodando no endereço `http://localhost:8501`.

### 5. Como Usar a Aplicação

1.  **Carregue o arquivo**: Clique em "Browse files" e selecione um arquivo CSV. Você pode usar o arquivo `data/tab_2.csv` para testar.
2.  **Filtre por CNAE**: Após o carregamento, um menu suspenso aparecerá. Selecione o CNAE das empresas que você deseja pesquisar.
3.  **Inicie a Busca**: Clique no botão "Buscar Perfis do Instagram". A aplicação começará a procurar os perfis, mostrando uma barra de progresso.
4.  **Veja e Baixe os Resultados**: Ao final da busca, os resultados serão exibidos em uma tabela. Use o botão "Baixar resultados em CSV" para salvar o arquivo.

## Estrutura do Projeto
- **`app.py`**: Arquivo principal da aplicação Streamlit.
- **`core/search.py`**: Contém toda a lógica de busca web.
- **`data/`**: Pasta para armazenar dados de exemplo.
- **`requirements.txt`**: Lista de dependências Python.