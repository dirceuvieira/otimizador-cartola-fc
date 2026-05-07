# 🚀 Especificação Técnica: Otimizador Cartola IA (Estilo Brasfoot)

## 1. Visão Geral e Objetivos
Este projeto é uma ferramenta pessoal de análise e escalação para o fantasy game Cartola FC. A arquitetura prioriza a **Simplicidade Pragmática**, focando em dados e lógica de otimização em vez de estética complexa.

- **Objetivo:** Maximizar a pontuação ou consistência financeira.
- **Interface:** Estilo analítico "Brasfoot" (Tabelas e Linhas) via Streamlit.
- **IA:** Modelos treinados localmente e resultados persistidos no Supabase.

## 2. Estrutura de Pastas (Screaming Architecture)
Organize o projeto para que as responsabilidades sejam claras e isoladas:

```text
/
├── app.py                # Entrada principal e UI Streamlit
├── core/
│   ├── optimizer.py      # Lógica matemática (Solver/Knapsack)
│   └── stats.py          # Cálculos de métricas (Efficiency, xP)
├── data/
│   ├── supabase_db.py    # Conexão e Queries ao Supabase
│   └── cartola_api.py    # Wrapper para API da Globo (opcional)
├── models/               # Armazena arquivos .pkl da IA (Local Only)
├── .env                  # Variáveis sensíveis (Tokens, DB_URL)
└── PROJETO_CARTOLA_IA.md # Este guia de contexto
```

## 3. Modelo de Dados (Contrato de Interface)
O sistema deve operar sobre DataFrames do Pandas com a seguinte estrutura mínima:

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `atleta_id` | int | ID único da API Globo |
| `apelido` | string | Nome do jogador |
| `posicao_id` | int | 1-GOL, 2-LAT, 3-ZAG, 4-MEI, 5-ATA, 6-TEC |
| `preco` | float | Custo atual em Cartoletas |
| `status_id` | int | Filtro (7 = Provável) |
| `xp_previsto`| float | Pontuação prevista pela IA local |
| `media_num` | float | Média histórica de pontos |

## 4. Lógica do Otimizador (The Solver)
Implementar a função de otimização no arquivo `core/optimizer.py` seguindo a lógica de **Programação Linear/Mochila**:

### 4.1 Modos de Estratégia:
1. **Pontuação Máxima (Mito):** Priorizar o maior `xp_previsto`.
2. **Consistência/Valorização:** Priorizar `Efficiency = media_num / preco`.

### 4.2 Algoritmo de Seleção (Pseudocódigo):
```python
def otimizar_escalacao(df, verba, esquema_tatico, modo):
    """
    df: DataFrame com atletas prováveis
    verba: float (Cartoletas disponíveis)
    esquema_tatico: dict (ex: {1:1, 2:2, 3:2, 4:3, 5:3, 6:1})
    """
    # 1. Aplicar métrica de score baseada no modo
    # 2. Ordenar atletas por score (descendente)
    # 3. Selecionar os N melhores para cada posição do esquema
    # 4. Validar se a soma dos preços <= verba
    # 5. Caso estoure, realizar substituições gulosas (Greedy)
```

## 5. Requisitos de UI (Streamlit - Estilo Brasfoot)
A interface deve seguir a ADR 003 (Analítica/Tabelas):

### Sidebar:
- Slider para `Orçamento Total`.
- Selectbox para `Esquema Tático`.
- Radio para `Estratégia da IA`.
- Botão "Sincronizar com PC Local" (Status de dados fresquinhos).

### Main Panel:
- **Tabela de Elite:** DataFrame estático mostrando os 11 titulares + técnico sugeridos, com linha de rodapé totalizando Custo e xP.
- **Mercado Inteligente:** `st.data_editor` com todos os jogadores, permitindo ordenação manual por qualquer coluna.

## 6. Decisões de Design e Trade-offs
- **Treinamento Local:** O modelo de ML é treinado no PC local para evitar custos de nuvem (TCO Zero).
- **Simplicidade de UI:** Sem gráficos 3D ou campos interativos; foco total em velocidade de leitura de tabela.
- **Resiliência:** Cache local de dados para funcionamento offline.