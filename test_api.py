#!/usr/bin/env python3
"""
Script de teste para verificar os dados da API do Cartola FC
"""
import sys
sys.path.append('.')

from data.cartola_api import CartolaAPI

if __name__ == "__main__":
    print("Testando API do Cartola FC...")
    try:
        df = CartolaAPI.get_mercado_data()
        print(f"✅ Sucesso! {len(df)} atletas carregados")

        # Verificar status_id únicos
        status_counts = df['status_id'].value_counts()
        print(f"Status IDs encontrados: {status_counts.to_dict()}")

        # Mostrar alguns atletas e seus status
        print("\nPrimeiros 10 atletas e seus status:")
        for _, row in df.head(10).iterrows():
            print(f"ID: {row['atleta_id']}, Nome: {row['apelido']}, Status: {row['status_id']}")

        # Mostrar alguns atletas prováveis
        provaveis = df[df['status_id'] == 7]
        print(f"Atletas prováveis: {len(provaveis)}")
        if len(provaveis) > 0:
            print(provaveis[['atleta_id', 'apelido', 'status_id']].head())

    except Exception as e:
        print(f"❌ Erro: {e}")