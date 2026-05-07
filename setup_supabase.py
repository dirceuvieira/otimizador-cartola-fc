#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar as tabelas no Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

def create_supabase_tables():
    """Cria as tabelas necessárias no Supabase"""

    # Carregar variáveis de ambiente
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Erro: SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")
        return False

    try:
        # Conectar ao Supabase
        client = create_client(url, key)
        print("✅ Conectado ao Supabase")

        # SQL para criar tabelas
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS atletas (
                atleta_id INTEGER PRIMARY KEY,
                apelido TEXT NOT NULL,
                posicao_id INTEGER NOT NULL,
                preco NUMERIC(10,2) NOT NULL DEFAULT 0,
                status_id INTEGER NOT NULL DEFAULT 1,
                xp_previsto NUMERIC(10,2),
                media_num NUMERIC(10,2) DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS previsoes (
                atleta_id INTEGER PRIMARY KEY,
                xp_previsto NUMERIC(10,2) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_atletas_status_id ON atletas(status_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_atletas_posicao_id ON atletas(posicao_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_previsoes_atleta_id ON previsoes(atleta_id);
            """
        ]

        # Executar comandos SQL
        for i, sql in enumerate(sql_commands, 1):
            try:
                client.rpc('exec_sql', {'sql': sql})
                print(f"✅ Comando SQL {i}/{len(sql_commands)} executado")
            except Exception as e:
                print(f"⚠️  Comando SQL {i} falhou (pode já existir): {e}")

        print("✅ Configuração das tabelas concluída!")
        print("\nTabelas criadas:")
        print("- atletas: Dados dos jogadores")
        print("- previsoes: Previsões de pontuação")
        print("\nAgora você pode executar: python train_local.py")

        return True

    except Exception as e:
        print(f"❌ Erro ao configurar Supabase: {e}")
        return False

if __name__ == "__main__":
    success = create_supabase_tables()
    exit(0 if success else 1)