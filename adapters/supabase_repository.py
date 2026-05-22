import os

from dotenv import load_dotenv
import pandas as pd
from supabase import create_client

from domain.repositories.athlete_repository import AthleteRepository
from domain.repositories.prediction_repository import PredictionRepository


def create_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if url and key:
        return create_client(url, key)

    try:
        import streamlit as st
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as exc:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment or Streamlit secrets"
        ) from exc


class SupabaseAthleteRepository(AthleteRepository):
    def __init__(self, client=None):
        self.client = client or create_supabase_client()

    def _load_table(self, table_name: str) -> pd.DataFrame:
        select_columns = (
            "atleta_id, apelido, posicao_id, preco, status_id, media_num, clube_nome, confronto"
        )
        response = self.client.table(table_name).select(select_columns).execute()
        return pd.DataFrame(response.data or [])

    def _merge_predictions(self, atletas: pd.DataFrame) -> pd.DataFrame:
        df_preds = self.client.table("previsoes").select(
            "atleta_id, xp_previsto, risco_atleta, timestamp_treino"
        ).execute()
        df_preds = pd.DataFrame(df_preds.data or [])
        if df_preds.empty:
            atletas["xp_previsto"] = 0.0
        else:
            atletas = atletas.merge(df_preds[["atleta_id", "xp_previsto"]], on="atleta_id", how="left")
            atletas["xp_previsto"] = atletas["xp_previsto"].fillna(0.0)
        return atletas

    def get_probable_atletas(self) -> pd.DataFrame:
        response = self.client.table("atletas").select(
            "atleta_id, apelido, posicao_id, preco, status_id, media_num, clube_nome, confronto"
        ).eq("status_id", 7).execute()
        df = pd.DataFrame(response.data or [])
        return self._merge_predictions(df)

    def get_all_atletas(self) -> pd.DataFrame:
        response = self.client.table("atletas").select(
            "atleta_id, apelido, posicao_id, preco, status_id, media_num, clube_nome, confronto"
        ).execute()
        df = pd.DataFrame(response.data or [])
        return self._merge_predictions(df)

    def upsert_athletes(self, df_market: pd.DataFrame) -> None:
        cols_to_upsert = [
            "atleta_id",
            "apelido",
            "posicao_id",
            "preco",
            "status_id",
            "media_num",
            "clube_nome",
            "confronto",
        ]
        df_athletes = df_market[[col for col in cols_to_upsert if col in df_market.columns]].copy()

        df_athletes["atleta_id"] = df_athletes["atleta_id"].astype(int)
        df_athletes["posicao_id"] = df_athletes["posicao_id"].astype(int)
        df_athletes["status_id"] = df_athletes["status_id"].astype(int)
        df_athletes["preco"] = pd.to_numeric(df_athletes["preco"], errors="coerce").fillna(0)
        df_athletes["media_num"] = pd.to_numeric(df_athletes["media_num"], errors="coerce").fillna(0)
        df_athletes["clube_nome"] = df_athletes["clube_nome"].fillna("")
        df_athletes["confronto"] = df_athletes["confronto"].fillna("")

        payload = df_athletes.to_dict(orient="records")
        batch_size = 1000
        for i in range(0, len(payload), batch_size):
            batch = payload[i : i + batch_size]
            self.client.table("atletas").upsert(batch).execute()


class SupabasePredictionRepository(PredictionRepository):
    def __init__(self, client=None):
        self.client = client or create_supabase_client()

    def get_previsoes(self) -> pd.DataFrame:
        response = self.client.table("previsoes").select(
            "atleta_id, xp_previsto, risco_atleta, timestamp_treino"
        ).execute()
        return pd.DataFrame(response.data or [])

    def get_timestamp_treino(self) -> str | None:
        response = self.client.table("previsoes").select("timestamp_treino").order("timestamp_treino", desc=True).limit(1).execute()
        if response.data:
            return response.data[0].get("timestamp_treino")
        return None

    def save_previsao(self, atleta_id: int, xp_previsto: float) -> None:
        self.client.table("previsoes").upsert({
            "atleta_id": atleta_id,
            "xp_previsto": xp_previsto,
        }).execute()

    def save_predictions(self, df_preds: pd.DataFrame) -> None:
        if df_preds.empty:
            return

        df_preds = df_preds.copy()
        df_preds["risco_atleta"] = df_preds.get("indice_risco", 0.0)
        df_preds["timestamp_treino"] = pd.Timestamp.now().isoformat()
        payload = df_preds[["atleta_id", "xp_previsto", "risco_atleta", "timestamp_treino"]].to_dict(orient="records")

        batch_size = 1000
        for i in range(0, len(payload), batch_size):
            batch = payload[i : i + batch_size]
            self.client.table("previsoes").upsert(batch).execute()

    # --- Matchup features persistence and training log helpers ---
    def upsert_matchup_features(self, df_features: pd.DataFrame) -> None:
        """Batch upsert matchup features into features_matchup table."""
        if df_features is None or df_features.empty:
            return
        df = df_features.copy()
        # Ensure expected columns
        cols = ["atleta_id", "rodada", "adversario_clube_id", "defesa_adversaria", "ataque_adversario", "finalizacoes_sofridas_adv", "timestamp_criacao"]
        present = [c for c in cols if c in df.columns]
        payload = df[present].to_dict(orient="records")
        batch_size = 500
        for i in range(0, len(payload), batch_size):
            batch = payload[i : i + batch_size]
            try:
                self.client.table("features_matchup").upsert(batch).execute()
            except Exception as e:
                error_msg = str(e)
                if "row-level security" in error_msg.lower() or "42501" in error_msg:
                    print(f"[WARN] RLS policy bloqueou inserção em features_matchup. Verifique políticas no Supabase.")
                    print(f"[WARN] Erro: {error_msg}")
                else:
                    print(f"[WARN] Erro ao upsert matchup features: {error_msg}")
                # Continue com próximo batch mesmo se esse falhar
                continue

    def log_training_execution(self, rodada: int, total_atletas: int, total_features: int, status: str = "success", error_msg: str | None = None) -> None:
        """Insert or upsert a training_log record."""
        payload = {
            "rodada": int(rodada),
            "total_atletas": int(total_atletas),
            "total_features_criadas": int(total_features),
            "status": status,
            "error_message": error_msg or None,
        }
        # Upsert by rodada and timestamp (simple approach: insert as new row)
        try:
            self.client.table("training_log").insert(payload).execute()
        except Exception as e:
            # Fallback to upsert if insert fails
            try:
                self.client.table("training_log").upsert(payload).execute()
            except Exception as e2:
                error_msg = str(e2)
                if "row-level security" in error_msg.lower() or "42501" in error_msg:
                    print(f"[WARN] RLS policy bloqueou inserção em training_log. Verifique políticas no Supabase.")
                else:
                    print(f"[WARN] Erro ao log training execution: {error_msg}")
