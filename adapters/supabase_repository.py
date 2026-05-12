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
