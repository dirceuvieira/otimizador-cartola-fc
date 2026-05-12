import unittest
from unittest.mock import patch

import pandas as pd

from application.use_cases.train_model_use_case import TrainModelUseCase
from domain.repositories.athlete_repository import AthleteRepository
from domain.repositories.prediction_repository import PredictionRepository


class FakeAthleteRepository(AthleteRepository):
    def __init__(self):
        self.upserted = None

    def get_probable_atletas(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_all_atletas(self) -> pd.DataFrame:
        raise NotImplementedError

    def upsert_athletes(self, df_market: pd.DataFrame) -> None:
        self.upserted = df_market.copy()


class FakePredictionRepository(PredictionRepository):
    def __init__(self):
        self.saved = None

    def get_previsoes(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_timestamp_treino(self) -> str | None:
        return None

    def save_previsao(self, atleta_id: int, xp_previsto: float) -> None:
        raise NotImplementedError

    def save_predictions(self, df_preds: pd.DataFrame) -> None:
        self.saved = df_preds.copy()


class TrainModelUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.athlete_repo = FakeAthleteRepository()
        self.prediction_repo = FakePredictionRepository()

        self.df_hist = pd.DataFrame(
            [
                {
                    "atleta_id": 1,
                    "posicao_id": 5,
                    "preco": 10.0,
                    "status_id": 7,
                    "media_num": 8.0,
                    "clube_id": 1,
                    "clube_nome": "A",
                    "rodada_id": 1,
                    "pontos": 8.0,
                    "casa": 1,
                    "jogo_id": 1,
                },
                {
                    "atleta_id": 1,
                    "posicao_id": 5,
                    "preco": 10.0,
                    "status_id": 7,
                    "media_num": 9.0,
                    "clube_id": 1,
                    "clube_nome": "A",
                    "rodada_id": 2,
                    "pontos": 9.0,
                    "casa": 1,
                    "jogo_id": 2,
                },
                {
                    "atleta_id": 2,
                    "posicao_id": 4,
                    "preco": 9.0,
                    "status_id": 7,
                    "media_num": 6.0,
                    "clube_id": 2,
                    "clube_nome": "B",
                    "rodada_id": 1,
                    "pontos": 6.0,
                    "casa": 0,
                    "jogo_id": 1,
                },
                {
                    "atleta_id": 2,
                    "posicao_id": 4,
                    "preco": 9.0,
                    "status_id": 7,
                    "media_num": 7.0,
                    "clube_id": 2,
                    "clube_nome": "B",
                    "rodada_id": 2,
                    "pontos": 7.0,
                    "casa": 0,
                    "jogo_id": 2,
                },
            ]
        )

        self.df_market = pd.DataFrame(
            [
                {
                    "atleta_id": 1,
                    "apelido": "Jogador A",
                    "posicao_id": 5,
                    "preco": 10.0,
                    "status_id": 7,
                    "media_num": 8.5,
                    "clube_id": 1,
                    "clube_nome": "A",
                    "confronto": "A x B",
                },
                {
                    "atleta_id": 2,
                    "apelido": "Jogador B",
                    "posicao_id": 4,
                    "preco": 9.0,
                    "status_id": 7,
                    "media_num": 6.5,
                    "clube_id": 2,
                    "clube_nome": "B",
                    "confronto": "B x A",
                },
            ]
        )

        self.df_partidas = pd.DataFrame()

    def test_execute_trains_model_and_persists_predictions(self):
        use_case = TrainModelUseCase(self.athlete_repo, self.prediction_repo)

        with patch("application.use_cases.train_model_use_case.training_helpers.load_csv_or_none", return_value=self.df_hist), patch(
            "application.use_cases.train_model_use_case.training_helpers.load_mercado_data", return_value=self.df_market
        ), patch(
            "application.use_cases.train_model_use_case.training_helpers.CartolaAPI.get_partidas", return_value=self.df_partidas
        ), patch(
            "application.use_cases.train_model_use_case.training_helpers.save_model", lambda model: None
        ):
            model, df_probables = use_case.execute()

        self.assertIsNotNone(model)
        self.assertFalse(df_probables.empty)
        self.assertIn("xp_previsto", df_probables.columns)
        self.assertIsNotNone(self.athlete_repo.upserted)
        self.assertIsNotNone(self.prediction_repo.saved)
        self.assertEqual(len(self.prediction_repo.saved), len(df_probables))
        self.assertEqual(self.athlete_repo.upserted.shape[0], self.df_market.shape[0])

    def test_execute_raises_when_training_data_insufficient(self):
        df_hist_small = pd.DataFrame(
            [{
                "atleta_id": 1,
                "posicao_id": 5,
                "preco": 10.0,
                "status_id": 7,
                "media_num": 8.0,
                "clube_id": 1,
                "clube_nome": "A",
                "rodada_id": 1,
                "pontos": 8.0,
                "casa": 1,
                "jogo_id": 1,
            }]
        )
        use_case = TrainModelUseCase(self.athlete_repo, self.prediction_repo)

        with patch("application.use_cases.train_model_use_case.training_helpers.load_csv_or_none", return_value=df_hist_small), patch(
            "application.use_cases.train_model_use_case.training_helpers.load_mercado_data", return_value=self.df_market
        ), patch(
            "application.use_cases.train_model_use_case.training_helpers.CartolaAPI.get_partidas", return_value=self.df_partidas
        ), patch(
            "application.use_cases.train_model_use_case.training_helpers.save_model", lambda model: None
        ):
            with self.assertRaises(ValueError):
                use_case.execute()


if __name__ == "__main__":
    unittest.main()
