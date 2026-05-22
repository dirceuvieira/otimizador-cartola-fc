-- Migration: Criar tabela features_matchup para armazenar features de confronto direto
-- Data: 2026-05-21
-- Descrição: Armazena features derivadas de confronto direto entre times (defesa adversária, ataque adversário, etc)

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

-- Índices para queries otimizadas
CREATE INDEX IF NOT EXISTS idx_features_matchup_atleta_id ON features_matchup(atleta_id);
CREATE INDEX IF NOT EXISTS idx_features_matchup_rodada ON features_matchup(rodada);
CREATE INDEX IF NOT EXISTS idx_features_matchup_adversario ON features_matchup(adversario_clube_id);
CREATE INDEX IF NOT EXISTS idx_features_matchup_timestamp ON features_matchup(timestamp_criacao DESC);

-- Comentários para documentação
COMMENT ON TABLE features_matchup IS 'Features derivadas de confronto direto entre times. Usadas para melhorar predições de pontos individuais.';
COMMENT ON COLUMN features_matchup.defesa_adversaria IS 'Média de gols sofridos pelo time adversário (últimas 5 rodadas). Relevante para atacantes.';
COMMENT ON COLUMN features_matchup.ataque_adversario IS 'Média de gols marcados pelo time adversário (últimas 5 rodadas). Relevante para defesa.';
COMMENT ON COLUMN features_matchup.finalizacoes_sofridas_adv IS 'Média de finalizações sofridas pelo time adversário (últimas 5 rodadas). Relevante para goleiros.';

-- Tabela de auditoria simples (opcional, para rastrear treinamentos)
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
