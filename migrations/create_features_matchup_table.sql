-- Migration: create features_matchup and training_log tables

BEGIN;

-- features_matchup: stores derived matchup features per athlete per rodada
CREATE TABLE IF NOT EXISTS public.features_matchup (
    id BIGSERIAL PRIMARY KEY,
    atleta_id BIGINT NOT NULL,
    rodada INTEGER NOT NULL,
    adversario_clube_id INTEGER NOT NULL DEFAULT 0,
    defesa_adversaria DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    ataque_adversario DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    finalizacoes_sofridas_adv DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    timestamp_criacao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Disable RLS for features_matchup to allow applications to write data
ALTER TABLE public.features_matchup DISABLE ROW LEVEL SECURITY;

-- Unique constraint to prevent duplicate athlete/rodada pairs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'features_matchup' AND c.conname = 'uq_features_matchup_atleta_rodada'
    ) THEN
        ALTER TABLE public.features_matchup
        ADD CONSTRAINT uq_features_matchup_atleta_rodada UNIQUE (atleta_id, rodada);
    END IF;
END$$;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_features_matchup_atleta_id ON public.features_matchup (atleta_id);
CREATE INDEX IF NOT EXISTS idx_features_matchup_rodada ON public.features_matchup (rodada);
CREATE INDEX IF NOT EXISTS idx_features_matchup_adversario ON public.features_matchup (adversario_clube_id);
CREATE INDEX IF NOT EXISTS idx_features_matchup_timestamp ON public.features_matchup (timestamp_criacao);

-- training_log: audit trail for feature generation runs
CREATE TABLE IF NOT EXISTS public.training_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp_treino TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    rodada INTEGER NOT NULL,
    total_atletas INTEGER NOT NULL DEFAULT 0,
    total_features_criadas INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT DEFAULT NULL
);

-- Disable RLS for training_log to allow applications to write data
ALTER TABLE public.training_log DISABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_training_log_rodada ON public.training_log (rodada);
CREATE INDEX IF NOT EXISTS idx_training_log_timestamp ON public.training_log (timestamp_treino);

COMMIT;

-- End of migration
