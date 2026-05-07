#!/usr/bin/env python3
"""
Script simples para testar a resposta crua da API do Cartola FC
"""
import requests

BASE_URL = "https://api.cartola.globo.com"

def test_api_raw():
    print("Testando resposta crua da API...")
    try:
        response = requests.get(f"{BASE_URL}/atletas/mercado", timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"Chaves do JSON raiz: {list(data.keys())}")

        if "atletas" in data:
            atletas = data["atletas"]
            print(f"Tipo de atletas: {type(atletas)}")
            print(f"Número de atletas: {len(atletas)}")

            if isinstance(atletas, list) and len(atletas) > 0:
                # Pegar primeiro atleta
                atleta = atletas[0]
                print(f"Primeiro atleta:")
                print(f"  Chaves: {list(atleta.keys())}")
                print(f"  atleta_id: {atleta.get('atleta_id')} (type: {type(atleta.get('atleta_id'))})")
                print(f"  status_id: {atleta.get('status_id')} (type: {type(atleta.get('status_id'))})")
                print(f"  apelido: {atleta.get('apelido')}")
                print(f"  posicao_id: {atleta.get('posicao_id')}")

            # Verificar se há chave 'status'
            if "status" in data:
                print(f"Chave 'status' encontrada: {data['status']}")

        return data

    except Exception as e:
        print(f"Erro: {e}")
        return None

if __name__ == "__main__":
    test_api_raw()