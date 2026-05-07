# 🧠 Especificação: Script de Treinamento e Alimentação (Local)

## 1. Objetivo
Criar um script Python robusto (`train_local.py`) que processe dados históricos de scouts, treine um modelo de Machine Learning e realize o `upsert` das predições no Supabase. Este script é o coração da estratégia de **Custo Zero** e **Processamento Híbrido**.

## 2. Fluxo de Execução (Pipeline)
O script deve seguir obrigatoriamente esta ordem:
1.  **Ingestão:** Carregar `historico_scouts.csv` e `mercado_atual.csv` da pasta `/data`.
2.  **Feature Engineering:**
    *   Calcular **Média Móvel** (últimos 5 jogos) por atleta.
    *   Calcular **Índice de Consistência** (Desvio padrão das últimas pontuações).
    *   Identificar **Mando de Campo** (Peso extra para quem joga em casa).
3.  **Treinamento:**
    *   Utilizar `RandomForestRegressor` da biblioteca `scikit-learn`.
    *   **Features:** `[media_movel, preco, posicao_id, mando_campo]`.
    *   **Target:** `pontos`.
4.  **Predição:** Gerar a coluna `xp_previsto` para todos os atletas com `status_id == 7` (Prováveis).
5.  **Persistência:**
    *   Salvar o modelo treinado em `/models/modelo_rodada_atual.pkl`.
    *   Fazer o upload apenas de `atleta_id` e `xp_previsto` para a tabela `jogadores_rodada` no Supabase.

## 3. Requisitos Técnicos e Resiliência
*   **Tratamento de Nulos:** Preencher valores nulos com `0` para evitar quebra no treinamento.
*   **Logging:** O script deve imprimir no terminal cada etapa concluída (Ex: `[INFO] Modelo treinado com sucesso`).
*   **Segurança:** Utilizar `python-dotenv` para carregar as chaves do Supabase do arquivo `.env`.
*   **Idempotência:** O upload para o Supabase deve usar a lógica de `upsert` (atualizar se o ID já existir, inserir se for novo).

## 4. Estrutura do Código (Sugestão para Copilot)
```python
def main():
    # 1. Carregar Dados
    # 2. Processar Features
    # 3. Treinar RandomForest
    # 4. Gerar XP Previsto
    # 5. Conectar no Supabase via supabase_db.py
    # 6. Finalizar
```
