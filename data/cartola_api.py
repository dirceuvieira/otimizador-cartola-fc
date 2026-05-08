import requests
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional


class CartolaAPI:
    """
    Wrapper para a API da Globo (Cartola FC).
    Recupera dados em tempo real e implementa cache local para resiliência.
    """

    BASE_URL = "https://api.cartola.globo.com"
    TIMEOUT = 10
    BACKUP_PATH = Path(__file__).parent / "backup_mercado.json"

    # Mapeamento de status_id
    STATUS_MAP = {
        "Provável": 7,
        "Dúvida": 6,
        "Suspenso": 5,
        "Noticiado": 4,
        "Contundido": 3,
        "Aposentado": 2,
        "Desconhecido": 1,
        7: 7,  # Já é provável
        6: 6,  # Já é dúvida
        5: 5,  # Já é suspenso
        4: 4,  # Já é noticiado
        3: 3,  # Já é contundido
        2: 2,  # Já é aposentado
        1: 1,  # Já é desconhecido
    }

    # Mapeamento de posição_id para nome
    POSICAO_MAP = {
        1: "GOL",
        2: "LAT",
        3: "ZAG",
        4: "MEI",
        5: "ATA",
        6: "TEC",
    }

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Retorna headers amigáveis para evitar bloqueios."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    @staticmethod
    def _save_backup(data: Dict[str, Any]) -> None:
        """Salva backup local de dados bem-sucedidos."""
        try:
            with open(CartolaAPI.BACKUP_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[WARN] Erro ao salvar backup: {e}")

    @staticmethod
    def map_status_id(status_value) -> int:
        """Mapeia status_id de qualquer formato para o valor correto."""
        if isinstance(status_value, str):
            # Tentar mapear string
            return CartolaAPI.STATUS_MAP.get(status_value, 1)
        elif isinstance(status_value, int):
            # Se já é número, verificar se precisa de mapeamento
            if status_value in CartolaAPI.STATUS_MAP:
                return CartolaAPI.STATUS_MAP[status_value]
            else:
                return status_value  # Já está correto
        else:
            return 1  # Desconhecido

    @staticmethod
    def get_mercado_data() -> pd.DataFrame:
        """
        Busca dados do mercado atual da API da Globo.
        Transforma a resposta em um DataFrame limpo com colunas do contrato de interface.
        Inclui scouts transformados em colunas individuais.

        Retorna:
            pd.DataFrame: Atletas com colunas [atleta_id, apelido, posicao_id, preco, status_id, media_num, + scouts]
        """
        try:
            # Requisição com timeout
            response = requests.get(
                f"{CartolaAPI.BASE_URL}/atletas/mercado",
                headers=CartolaAPI._get_headers(),
                timeout=CartolaAPI.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            CartolaAPI._save_backup(data)

        except Exception as e:
            print(f"[WARN] Falha na API: {e}. Tentando carregar backup...")
            data = CartolaAPI._load_backup()
            if data is None:
                raise RuntimeError(f"Erro ao conectar à API do Cartola FC: {e}")

        try:
            # Extrair lista de atletas
            if isinstance(data, dict) and "atletas" in data:
                atletas_data = data["atletas"]
            elif isinstance(data, list):
                atletas_data = data
            else:
                atletas_data = data

            # Extrair mapeamento de status da API
            status_map_api = {}
            if isinstance(data, dict) and "status" in data:
                for status_key, status_info in data["status"].items():
                    status_id = int(status_key)
                    status_nome = status_info.get("nome", "").lower()
                    # Mapear para nossos códigos
                    if "provável" in status_nome:
                        status_map_api[status_id] = 7
                    elif "dúvida" in status_nome:
                        status_map_api[status_id] = 6
                    elif "suspenso" in status_nome:
                        status_map_api[status_id] = 5
                    elif "contundido" in status_nome:
                        status_map_api[status_id] = 3
                    elif "nulo" in status_nome or "desconhecido" in status_nome:
                        status_map_api[status_id] = 1
                    else:
                        status_map_api[status_id] = 1  # Default

            # Se atletas_data é dict, iterar como dict; se é list, iterar como list
            rows = []
            
            if isinstance(atletas_data, dict):
                # Estrutura: {"123": {...}, "456": {...}}
                for atleta_id, atleta_info in atletas_data.items():
                    if not isinstance(atleta_info, dict):
                        continue
                    
                    try:
                        atleta_id_int = int(atleta_id)
                        apelido = str(atleta_info.get("apelido", "")).strip()
                        posicao_id = int(atleta_info.get("posicao_id", 0))
                        preco = float(atleta_info.get("preco_num", 0.0))
                        status_raw = atleta_info.get("status_id", 1)

                        # Mapear status_id usando o mapeamento da API
                        status_id = status_map_api.get(status_raw, status_raw)

                        # Média histórica
                        media_num = float(atleta_info.get("media_num", 0.0))

                        # Construir row base
                        row = {
                            "atleta_id": atleta_id_int,
                            "apelido": apelido,
                            "posicao_id": posicao_id,
                            "preco": preco,
                            "status_id": status_id,
                            "media_num": media_num,
                            "clube_id": int(atleta_info.get("clube_id", 0) or 0),
                            "clube_nome": str(atleta_info.get("clube", {}).get("nome", "") or "").strip(),
                            "rodada_id": int(atleta_info.get("rodada_id", 0) or 0),
                        }

                        # Transformar scouts em colunas
                        scouts = atleta_info.get("scout", {})
                        if isinstance(scouts, dict):
                            for scout_key, scout_value in scouts.items():
                                row[f"scout_{scout_key}"] = float(scout_value) if scout_value else 0.0

                        rows.append(row)

                    except (ValueError, TypeError):
                        continue
            
            elif isinstance(atletas_data, list):
                # Estrutura: [{...}, {...}]
                for atleta_info in atletas_data:
                    if not isinstance(atleta_info, dict):
                        continue
                    
                    try:
                        atleta_id_int = int(atleta_info.get("atleta_id") or atleta_info.get("id", 0))
                        apelido = str(atleta_info.get("apelido", "")).strip()
                        posicao_id = int(atleta_info.get("posicao_id", 0))
                        preco = float(atleta_info.get("preco_num", 0.0))
                        status_raw = atleta_info.get("status_id", 1)

                        # Mapear status_id usando o mapeamento da API
                        status_id = status_map_api.get(status_raw, status_raw)

                        # Média histórica
                        media_num = float(atleta_info.get("media_num", 0.0))

                        # Construir row base
                        row = {
                            "atleta_id": atleta_id_int,
                            "apelido": apelido,
                            "posicao_id": posicao_id,
                            "preco": preco,
                            "status_id": status_id,
                            "media_num": media_num,
                            "clube_id": int(atleta_info.get("clube_id", 0) or 0),
                            "clube_nome": str(atleta_info.get("clube", {}).get("nome", "") or "").strip(),
                            "rodada_id": int(atleta_info.get("rodada_id", 0) or 0),
                        }

                        # Transformar scouts em colunas
                        scouts = atleta_info.get("scout", {})
                        if isinstance(scouts, dict):
                            for scout_key, scout_value in scouts.items():
                                row[f"scout_{scout_key}"] = float(scout_value) if scout_value else 0.0

                        rows.append(row)

                    except (ValueError, TypeError):
                        continue

            if not rows:
                raise ValueError("Nenhum atleta válido encontrado nos dados")

            df = pd.DataFrame(rows)

            # Garantir tipos de dados corretos para colunas base
            base_dtypes = {
                "atleta_id": "int64",
                "apelido": "object",
                "posicao_id": "int64",
                "preco": "float64",
                "status_id": "int64",
                "media_num": "float64",
            }
            for col in base_dtypes:
                if col in df.columns:
                    df[col] = df[col].astype(base_dtypes[col])

            # Preencher scouts ausentes com 0
            scout_cols = [col for col in df.columns if col.startswith("scout_")]
            for col in scout_cols:
                df[col] = df[col].fillna(0.0).astype("float64")

            return df

        except Exception as e:
            raise RuntimeError(f"Erro ao processar dados do mercado: {e}")

    @staticmethod
    def get_partidas() -> pd.DataFrame:
        """
        Busca dados das partidas da rodada atual.
        Útil para identificar mando de campo e adversários.

        Retorna:
            pd.DataFrame: Partidas com colunas [partida_id, rodada, time_casa_id, time_visitante_id, clube_casa, clube_visitante, mando_campo]
        """
        try:
            response = requests.get(
                f"{CartolaAPI.BASE_URL}/partidas",
                headers=CartolaAPI._get_headers(),
                timeout=CartolaAPI.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            rows = []
            for partida_info in data.get("partidas", []):
                try:
                    row = {
                        "partida_id": int(partida_info.get("partida_id", 0)),
                        "rodada": int(partida_info.get("rodada", 0)),
                        "time_casa_id": int(partida_info.get("clube_casa_id", 0)),
                        "time_visitante_id": int(partida_info.get("clube_visitante_id", 0)),
                        "clube_casa": str(partida_info.get("clube_casa", {}).get("nome", "")).strip(),
                        "clube_visitante": str(partida_info.get("clube_visitante", {}).get("nome", "")).strip(),
                    }
                    rows.append(row)
                except (ValueError, TypeError):
                    continue

            df = pd.DataFrame(rows)
            return df

        except Exception as e:
            raise RuntimeError(f"Erro ao buscar partidas: {e}")

    @staticmethod
    def get_scouts_historico(atleta_id: int, limite: int = 100) -> pd.DataFrame:
        """
        Busca histórico de scouts para um atleta específico.
        (Implementação simplificada; adaptar conforme resposta real da API)

        Args:
            atleta_id (int): ID do atleta.
            limite (int): Número máximo de scouts a recuperar (padrão: 100).

        Retorna:
            pd.DataFrame: Histórico de scouts com colunas [jogo_id, rodada, pontos, scouts_*]
        """
        try:
            response = requests.get(
                f"{CartolaAPI.BASE_URL}/atleta/{atleta_id}/estatisticas",
                headers=CartolaAPI._get_headers(),
                timeout=CartolaAPI.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            rows = []
            for game_info in data.get("historico", [])[:limite]:
                try:
                    row = {
                        "atleta_id": atleta_id,
                        "jogo_id": int(game_info.get("jogo_id", 0)),
                        "rodada": int(game_info.get("rodada", 0)),
                        "pontos": float(game_info.get("pontos", 0.0)),
                    }

                    # Scouts como colunas
                    scouts = game_info.get("scout", {})
                    if isinstance(scouts, dict):
                        for scout_key, scout_value in scouts.items():
                            row[f"scout_{scout_key}"] = float(scout_value) if scout_value else 0.0

                    rows.append(row)
                except (ValueError, TypeError):
                    continue

            df = pd.DataFrame(rows)
            return df

        except Exception as e:
            print(f"[WARN] Erro ao buscar scout do atleta {atleta_id}: {e}")
            return pd.DataFrame()
