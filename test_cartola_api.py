#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do CartolaAPI com mapeamento de status corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.cartola_api import CartolaAPI
import pandas as pd

def test_cartola_api_status_mapping():
    """Testa se o mapeamento de status está funcionando corretamente"""
    print("Testando CartolaAPI com mapeamento de status...")

    # Criar instância da API
    api = CartolaAPI()

    try:
        # Buscar dados do mercado
        df = api.get_mercado_data()

        if df is None or df.empty:
            print("❌ Erro: Não foi possível obter dados do mercado")
            return False

        print(f"✅ Dados obtidos: {len(df)} atletas")

        # Verificar distribuição de status_id
        status_counts = df['status_id'].value_counts().sort_index()
        print("\nDistribuição de status_id:")
        for status_id, count in status_counts.items():
            print(f"  Status {status_id}: {count} atletas")

        # Verificar se temos atletas com status 7 (Provável)
        provaveis = df[df['status_id'] == 7]
        if not provaveis.empty:
            print(f"\n✅ Encontrados {len(provaveis)} atletas 'Prováveis'")
            print("Exemplos:")
            for _, row in provaveis.head(3).iterrows():
                print(f"  - {row['apelido']} (ID: {row['atleta_id']})")
        else:
            print("\n❌ Nenhum atleta com status 'Provável' encontrado")

        # Verificar se temos atletas com status 6 (Dúvida/Nulo)
        duvidosos = df[df['status_id'] == 6]
        if not duvidosos.empty:
            print(f"\n✅ Encontrados {len(duvidosos)} atletas 'Dúvida/Nulo'")
            print("Exemplos:")
            for _, row in duvidosos.head(3).iterrows():
                print(f"  - {row['apelido']} (ID: {row['atleta_id']})")

        # Verificar colunas de scouts
        scout_cols = [col for col in df.columns if col.startswith('scout_')]
        print(f"\n✅ Colunas de scouts encontradas: {len(scout_cols)}")
        if scout_cols:
            print(f"Exemplos: {scout_cols[:5]}")

        return True

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    success = test_cartola_api_status_mapping()
    sys.exit(0 if success else 1)