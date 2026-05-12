from typing import List

import numpy as np
import pandas as pd

from data.cartola_api import CartolaAPI
from domain.repositories.athlete_repository import AthleteRepository
from domain.repositories.prediction_repository import PredictionRepository


class GetRetrospectiveUseCase:
    def __init__(
        self,
        athlete_repository: AthleteRepository,
        prediction_repository: PredictionRepository,
    ):
        self.athlete_repository = athlete_repository
        self.prediction_repository = prediction_repository

    def execute(self, posicao_id: int | None = None, rodada: int | None = None) -> pd.DataFrame:
        """Monta a tabela de retrospectiva entre previsões e resultados reais."""
        df_athletes = self.athlete_repository.get_all_atletas()

        if df_athletes is None or df_athletes.empty:
            return pd.DataFrame()

        # Verificar se tem previsões (xp_previsto)
        if "xp_previsto" not in df_athletes.columns:
            return pd.DataFrame()

        if posicao_id is not None:
            df_athletes = df_athletes[df_athletes["posicao_id"] == posicao_id]

        if df_athletes.empty:
            return pd.DataFrame()

        df = df_athletes.copy()

        if rodada is not None and rodada > 0:
            df_results = CartolaAPI.get_pontuados_by_rodada(int(rodada))
        else:
            df_results = CartolaAPI.get_latest_round_results(df["atleta_id"].tolist())

        if not df_results.empty:
            df_results = df_results[df_results["atleta_id"].isin(df["atleta_id"])]
            df = df.merge(
                df_results[["atleta_id", "rodada", "pontos"]],
                on="atleta_id",
                how="left",
            )
        else:
            df["rodada"] = pd.NA
            df["pontos"] = pd.NA

        df = df.rename(columns={"pontos": "pontos_reais"})
        df["pontos_reais"] = pd.to_numeric(df["pontos_reais"], errors="coerce")
        df["erro_assinado"] = df["xp_previsto"] - df["pontos_reais"]
        df["erro_absoluto"] = df["erro_assinado"].abs()
        df["erro_pct"] = df["erro_assinado"] / df["pontos_reais"].replace({0: np.nan})
        df["erro_pct"] = df["erro_pct"].round(4)
        df["erro_pct"] = df["erro_pct"].fillna(0.0)

        return df
