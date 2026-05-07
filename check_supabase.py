#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar e criar tabelas no Supabase usando REST API
"""

import os
import requests
from dotenv import load_dotenv

def check_and_create_tables():
    """Verifica e cria tabelas usando REST API do Supabase"""

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ SUPABASE_URL e SUPABASE_KEY não encontrados no .env")
        return False

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "apikey": key
    }

    # Verificar se tabela previsoes existe
    try:
        response = requests.get(f"{url}/rest/v1/previsoes?limit=1", headers=headers)
        if response.status_code == 200:
            print("✅ Tabela 'previsoes' já existe")
        else:
            print(f"⚠️  Tabela 'previsoes' não encontrada (status: {response.status_code})")
            # Tentar criar via SQL
            create_table_sql(url, key, "previsoes")
    except Exception as e:
        print(f"Erro ao verificar tabela previsoes: {e}")
        create_table_sql(url, key, "previsoes")

    # Verificar se tabela atletas existe
    try:
        response = requests.get(f"{url}/rest/v1/atletas?limit=1", headers=headers)
        if response.status_code == 200:
            print("✅ Tabela 'atletas' já existe")
        else:
            print(f"⚠️  Tabela 'atletas' não encontrada (status: {response.status_code})")
            create_table_sql(url, key, "atletas")
    except Exception as e:
        print(f"Erro ao verificar tabela atletas: {e}")
        create_table_sql(url, key, "atletas")

    return True

def create_table_sql(url, key, table_name):
    """Cria tabela via SQL usando a API do Supabase"""

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "apikey": key
    }

    if table_name == "previsoes":
        sql = """
        CREATE TABLE IF NOT EXISTS previsoes (
            atleta_id INTEGER PRIMARY KEY,
            xp_previsto NUMERIC(10,2) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
    elif table_name == "atletas":
        sql = """
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
        """
    else:
        print(f"❌ Tabela desconhecida: {table_name}")
        return

    try:
        # Usar o endpoint de SQL do Supabase
        sql_url = f"{url}/rest/v1/rpc/exec_sql"
        payload = {"sql": sql}

        response = requests.post(sql_url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Tabela '{table_name}' criada com sucesso")
        else:
            print(f"❌ Erro ao criar tabela '{table_name}': {response.status_code} - {response.text}")

            # Fallback: tentar inserir um registro de teste para forçar criação
            print("Tentando método alternativo...")
            create_table_fallback(url, key, table_name)

    except Exception as e:
        print(f"❌ Erro na criação da tabela '{table_name}': {e}")
        create_table_fallback(url, key, table_name)

def create_table_fallback(url, key, table_name):
    """Método alternativo para criar tabelas via inserção"""

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "apikey": key,
        "Prefer": "resolution=merge-duplicates"
    }

    if table_name == "previsoes":
        # Tentar inserir um registro de teste
        test_data = {"atleta_id": 999999, "xp_previsto": 0.0}
        response = requests.post(f"{url}/rest/v1/previsoes", headers=headers, json=test_data)

        if response.status_code in [201, 409]:  # 201 = criado, 409 = conflito (já existe)
            print(f"✅ Tabela '{table_name}' verificada/criada via fallback")
            # Remover registro de teste
            requests.delete(f"{url}/rest/v1/previsoes?atleta_id=eq.999999", headers=headers)
        else:
            print(f"❌ Falha no fallback para '{table_name}': {response.status_code} - {response.text}")

    elif table_name == "atletas":
        test_data = {
            "atleta_id": 999999,
            "apelido": "TESTE",
            "posicao_id": 1,
            "preco": 0.0,
            "status_id": 1,
            "media_num": 0.0
        }
        response = requests.post(f"{url}/rest/v1/atletas", headers=headers, json=test_data)

        if response.status_code in [201, 409]:
            print(f"✅ Tabela '{table_name}' verificada/criada via fallback")
            # Remover registro de teste
            requests.delete(f"{url}/rest/v1/atletas?atleta_id=eq.999999", headers=headers)
        else:
            print(f"❌ Falha no fallback para '{table_name}': {response.status_code} - {response.text}")

if __name__ == "__main__":
    success = check_and_create_tables()
    if success:
        print("\n🎉 Verificação concluída! Agora execute: python train_local.py")
    exit(0 if success else 1)