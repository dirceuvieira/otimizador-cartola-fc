# 🌐 Especificação: Coletor de Dados Oficiais (Cartola API)

## 1. Objetivo
Implementar o arquivo `data/cartola_api.py` para extrair dados em tempo real da API oficial da Globo. Este script será a fonte primária para alimentar o `train_local.py`.

## 2. Endpoints Principais
O script deve realizar requisições `GET` para:
*   **Mercado/Atletas:** `[https://api.cartola.globo.com/atletas/mercado](https://api.cartola.globo.com/atletas/mercado)` (Dados da rodada atual, preços e status).
*   **Clubes:** Incluído no JSON de atletas (para mapear escudos e nomes).
*   **Partidas:** `[https://api.cartola.globo.com/partidas](https://api.cartola.globo.com/partidas)` (Para identificar mando de campo e adversários).

## 3. Lógica de Implementação
1.  **Request:** Utilizar a biblioteca `requests` com um `User-Agent` amigável para evitar bloqueios.
2.  **Mapeamento de Dados:**
    *   Extrair o dicionário de `atletas`.
    *   Mapear `clube_id` para o nome do clube.
    *   Mapear `posicao_id` para o nome da posição (GOL, LAT, ZAG, etc.).
3.  **Processamento:**
    *   Converter o JSON retornado em um DataFrame do Pandas.
    *   Tratar a coluna `scout` (que vem como um dicionário aninhado) para que cada scout (DS, G, A, etc.) vire uma coluna individual no DataFrame.

## 4. Integração com o Pipeline de Treinamento
No arquivo `train_local.py`, a função de carga de dados deve ser alterada de:
`df = pd.read_csv('data/mercado_atual.csv')` 
Para:
`df = CartolaAPI().get_mercado_data()`

## 5. Requisitos de Resiliência (Design for Failure)
*   **Timeout:** Configurar um timeout de 10 segundos nas requisições.
*   **Cache de Segurança:** Sempre que uma requisição for bem-sucedida, salvar uma cópia local em `data/backup_mercado.json`. Caso a API esteja fora do ar, o script deve carregar o backup automaticamente.
