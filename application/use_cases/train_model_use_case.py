from typing import Optional, Tuple

import pandas as pd

import train_local as training_helpers
from domain.repositories.athlete_repository import AthleteRepository
from domain.repositories.prediction_repository import PredictionRepository


class TrainModelUseCase:
    def __init__(self, athlete_repository: AthleteRepository, prediction_repository: PredictionRepository):
        self.athlete_repository = athlete_repository
        self.prediction_repository = prediction_repository

    def execute(self) -> Tuple[Optional[object], pd.DataFrame]:
        """Treina o modelo e persiste atletas e previsões no repositório."""
        df_hist = training_helpers.load_csv_or_none("historico_scouts.csv")
        if df_hist is None:
            df_hist = training_helpers.download_and_save_historico()

        df_market = training_helpers.load_mercado_data()
        df_partidas = training_helpers.CartolaAPI.get_partidas()

        df_hist = df_hist.fillna(0)
        df_market = df_market.fillna(0)

        df_train = training_helpers.prepare_training_data(df_hist)
        if df_train.empty:
            raise ValueError("Dados insuficientes para treinar o modelo")

        model = training_helpers.train_model(df_train)
        training_helpers.save_model(model)

        df_predict = training_helpers.build_prediction_dataset(df_hist, df_market, df_partidas)
        df_probables = df_predict[df_predict["status_id"] == 7].copy()
        if df_probables.empty:
            return model, pd.DataFrame()

        feature_cols = [
            "media_movel",
            "indice_risco",
            "preco",
            "posicao_id",
            "mando_campo",
            "scouts_cedidos_adv",
            "forca_mandante",
            "finalizacoes_acumuladas",
        ]
        df_probables["xp_previsto"] = model.predict(df_probables[feature_cols].astype(float))

        self.athlete_repository.upsert_athletes(df_market)
        self.prediction_repository.save_predictions(df_probables)

        return model, df_probables
