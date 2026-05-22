"""
Script para executar migrations no Supabase via API Python.
Cria as tabelas necessárias para armazenar features de matchup.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")

def run_migration():
    """Executa o script de migration SQL no Supabase."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Ler o arquivo de migration
    migration_path = Path(__file__).parent / "migrations" / "create_features_matchup_table.sql"
    
    if not migration_path.exists():
        print(f"Erro: Arquivo de migration não encontrado em {migration_path}")
        return False
    
    with open(migration_path, "r", encoding="utf-8") as f:
        sql_script = f.read()
    
    print("Iniciando migration no Supabase...")
    print("=" * 70)
    
    try:
        # O Supabase Python client não tem método direto para RPC de SQL arbitrário
        # Vamos usar a abordagem de chamar via rpc ou usando o admin client
        # A forma mais simples é usar o client.from_ para executar queries
        
        # Dividir o script em statements individuais
        statements = [s.strip() for s in sql_script.split(";") if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            print(f"\nExecutando statement {i}/{len(statements)}...")
            print(f"Preview: {statement[:80]}...")
            
            try:
                # Usar a API de query do Supabase (se disponível)
                # Alternativa: usar postgres-py ou similar
                result = client.postgrest.client.execute(statement)
                print(f"✓ Statement {i} executado com sucesso")
            except Exception as e:
                # Se falhar com execute, tentar com rpc
                print(f"⚠ Tentando via RPC...")
                try:
                    result = client.rpc("run_sql", {"sql": statement}).execute()
                    print(f"✓ Statement {i} executado com sucesso via RPC")
                except Exception as rpc_error:
                    print(f"✗ Erro ao executar statement {i}: {rpc_error}")
                    return False
        
        print("\n" + "=" * 70)
        print("✓ Migration concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro durante migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
