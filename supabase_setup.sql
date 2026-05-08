-- Script SQL para criar as tabelas necessárias no Supabase
-- Execute este script no SQL Editor do Supabase

-- Tabela para armazenar dados dos atletas
CREATE TABLE IF NOT EXISTS atletas (
    atleta_id INTEGER PRIMARY KEY,
    apelido TEXT NOT NULL,
    posicao_id INTEGER NOT NULL,
    preco NUMERIC(10,2) NOT NULL DEFAULT 0,
    status_id INTEGER NOT NULL DEFAULT 1,
    media_num NUMERIC(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela para armazenar previsões de pontuação
CREATE TABLE IF NOT EXISTS previsoes (
    atleta_id INTEGER PRIMARY KEY,
    xp_previsto NUMERIC(10,2) NOT NULL,
    risco_atleta NUMERIC(10,2),
    timestamp_treino TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Adicionar colunas se não existirem (para tabelas já criadas)
ALTER TABLE atletas ADD COLUMN IF NOT EXISTS clube_nome TEXT;
ALTER TABLE atletas ADD COLUMN IF NOT EXISTS confronto TEXT;
ALTER TABLE previsoes ADD COLUMN IF NOT EXISTS risco_atleta NUMERIC(10,2);
ALTER TABLE previsoes ADD COLUMN IF NOT EXISTS timestamp_treino TIMESTAMP WITH TIME ZONE;

-- Políticas RLS (Row Level Security) - opcional, mas recomendado
ALTER TABLE atletas ENABLE ROW LEVEL SECURITY;
ALTER TABLE previsoes ENABLE ROW LEVEL SECURITY;

-- Políticas para permitir leitura/escrita (ajuste conforme necessário)
CREATE POLICY "Permitir leitura de atletas" ON atletas FOR SELECT USING (true);
CREATE POLICY "Permitir escrita de atletas" ON atletas FOR ALL USING (true);

CREATE POLICY "Permitir leitura de previsoes" ON previsoes FOR SELECT USING (true);
CREATE POLICY "Permitir escrita de previsoes" ON previsoes FOR ALL USING (true);