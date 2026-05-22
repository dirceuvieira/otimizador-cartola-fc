# MIGRATION: Features Matchup para Cartola FC

## Opção 1: Rodar diretamente no Supabase (Recomendado - Mais Rápido)

### Passos:
1. Vá até https://app.supabase.com
2. Selecione seu projeto
3. Clique em **SQL Editor** (ou **SQL** no menu lateral)
4. Clique em **New Query**
5. Cole o conteúdo abaixo
6. Clique em **Run**

### Script SQL:

```sql
-- Migration: Criar tabela features_matchup para armazenar features de confronto direto
-- Data: 2026-05-21

CREATE TABLE IF NOT EXISTS features_matchup (
  id BIGSERIAL PRIMARY KEY,
  atleta_id INTEGER NOT NULL,
  rodada INTEGER NOT NULL,
  adversario_clube_id INTEGER,
  defesa_adversaria FLOAT8 DEFAULT 0.0,
  ataque_adversario FLOAT8 DEFAULT 0.0,
  finalizacoes_sofridas_adv FLOAT8 DEFAULT 0.0,
  timestamp_criacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(atleta_id, rodada)
);

CREATE INDEX IF NOT EXISTS idx_features_matchup_atleta_id ON features_matchup(atleta_id);
CREATE INDEX IF NOT EXISTS idx_features_matchup_rodada ON features_matchup(rodada);
CREATE INDEX IF NOT EXISTS idx_features_matchup_adversario ON features_matchup(adversario_clube_id);
CREATE INDEX IF NOT EXISTS idx_features_matchup_timestamp ON features_matchup(timestamp_criacao DESC);

COMMENT ON TABLE features_matchup IS 'Features derivadas de confronto direto entre times. Usadas para melhorar predições de pontos individuais.';
COMMENT ON COLUMN features_matchup.defesa_adversaria IS 'Média de gols sofridos pelo time adversário (últimas 5 rodadas). Relevante para atacantes.';
COMMENT ON COLUMN features_matchup.ataque_adversario IS 'Média de gols marcados pelo time adversário (últimas 5 rodadas). Relevante para defesa.';
COMMENT ON COLUMN features_matchup.finalizacoes_sofridas_adv IS 'Média de finalizações sofridas pelo time adversário (últimas 5 rodadas). Relevante para goleiros.';

CREATE TABLE IF NOT EXISTS training_log (
  id BIGSERIAL PRIMARY KEY,
  timestamp_treino TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  rodada INTEGER,
  total_atletas INTEGER,
  total_features_criadas INTEGER,
  status TEXT DEFAULT 'success',
  error_message TEXT,
  UNIQUE(timestamp_treino, rodada)
);

CREATE INDEX IF NOT EXISTS idx_training_log_rodada ON training_log(rodada);
CREATE INDEX IF NOT EXISTS idx_training_log_timestamp ON training_log(timestamp_treino DESC);
```

## Opção 2: Rodar via Python (Alternativa)

Se preferir rodar via script Python:

```bash
cd c:\Users\fabricio\Documents\Dirceu\cartola-fc
python run_migration.py
```

⚠️ **Nota:** O script Python requer que o Supabase Python client tenha suporte para RPC SQL.
Se receber erro, prefira a **Opção 1** (console do Supabase).

---

## Verificação: Confirmar que as tabelas foram criadas

```sql
-- Listar as tabelas criadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('features_matchup', 'training_log');

-- Ver estrutura da tabela features_matchup
\d features_matchup

-- Ver índices criados
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('features_matchup', 'training_log');
```

---

## Estrutura das Tabelas Criadas

### `features_matchup`
Armazena features calculadas a partir de confrontos diretos:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | BIGSERIAL | ID único (chave primária) |
| `atleta_id` | INTEGER | ID do atleta |
| `rodada` | INTEGER | Número da rodada |
| `adversario_clube_id` | INTEGER | ID do time adversário |
| `defesa_adversaria` | FLOAT8 | Média de gols sofridos pelo adversário (últimas 5 rodadas) |
| `ataque_adversario` | FLOAT8 | Média de gols marcados pelo adversário (últimas 5 rodadas) |
| `finalizacoes_sofridas_adv` | FLOAT8 | Média de finalizações sofridas pelo adversário |
| `timestamp_criacao` | TIMESTAMP | Quando a feature foi calculada |

**Constraint:** `UNIQUE(atleta_id, rodada)` - Garante uma única feature por atleta/rodada

### `training_log`
Rastreamento de execuções de treinamento (opcional):

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | BIGSERIAL | ID único |
| `timestamp_treino` | TIMESTAMP | Quando o treinamento foi executado |
| `rodada` | INTEGER | Rodada processada |
| `total_atletas` | INTEGER | Quantos atletas foram processados |
| `total_features_criadas` | INTEGER | Quantas features foram criadas |
| `status` | TEXT | 'success' ou 'error' |
| `error_message` | TEXT | Mensagem de erro (se houver) |

---

## Próximos Passos

Após criar as tabelas:

1. ✅ Criar funções em `train_local.py` para calcular stats por clube
2. ✅ Enriquecer dataset com features de matchup
3. ✅ Salvar features no Supabase após treino
4. ✅ Criar UI no Streamlit para visualizar detalhes do atleta
