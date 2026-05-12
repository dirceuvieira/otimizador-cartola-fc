import pandas as pd

from application.use_cases.get_retrospective_use_case import GetRetrospectiveUseCase


class DummyAthleteRepo:
    def get_all_atletas(self):
        return pd.DataFrame(
            [
                {
                    "atleta_id": 1,
                    "apelido": "Jogador A",
                    "posicao_id": 5,
                    "preco": 20.0,
                    "status_id": 7,
                    "media_num": 8.0,
                    "clube_nome": "Time X",
                    "confronto": "X x Y",
                },
                {
                    "atleta_id": 2,
                    "apelido": "Jogador B",
                    "posicao_id": 4,
                    "preco": 15.0,
                    "status_id": 7,
                    "media_num": 7.0,
                    "clube_nome": "Time Y",
                    "confronto": "Y x X",
                },
            ]
        )

    def get_probable_atletas(self):
        raise NotImplementedError

    def upsert_athletes(self, df_market):
        raise NotImplementedError


class DummyPredictionRepo:
    def get_previsoes(self):
        return pd.DataFrame(
            [
                {"atleta_id": 1, "xp_previsto": 12.0},
                {"atleta_id": 2, "xp_previsto": 6.5},
            ]
        )

    def get_timestamp_treino(self):
        return None

    def save_previsao(self, atleta_id: int, xp_previsto: float):
        raise NotImplementedError

    def save_predictions(self, df_preds):
        raise NotImplementedError


def test_get_retrospective_calculates_error(monkeypatch):
    def fake_latest_round_results(atleta_ids):
        return pd.DataFrame(
            [
                {"atleta_id": 1, "rodada": 15, "pontos": 10.0},
                {"atleta_id": 2, "rodada": 15, "pontos": 5.0},
            ]
        )

    monkeypatch.setattr(
        "application.use_cases.get_retrospective_use_case.CartolaAPI.get_latest_round_results",
        fake_latest_round_results,
    )

    use_case = GetRetrospectiveUseCase(DummyAthleteRepo(), DummyPredictionRepo())
    df = use_case.execute()

    assert len(df) == 2
    assert df.loc[df["atleta_id"] == 1, "pontos_reais"].iloc[0] == 10.0
    assert df.loc[df["atleta_id"] == 1, "erro_absoluto"].iloc[0] == 2.0
    assert df.loc[df["atleta_id"] == 2, "erro_assinado"].iloc[0] == 1.5
    assert "erro_pct" in df.columns


def test_get_retrospective_filters_by_position_and_round_api(monkeypatch):
    class PositionDummyAthleteRepo:
        def get_all_atletas(self):
            return pd.DataFrame(
                [
                    {
                        "atleta_id": 1,
                        "apelido": "Jogador A",
                        "posicao_id": 6,
                        "preco": 20.0,
                        "status_id": 7,
                        "media_num": 8.0,
                        "clube_nome": "Time X",
                        "confronto": "X x Y",
                    },
                    {
                        "atleta_id": 2,
                        "apelido": "Jogador B",
                        "posicao_id": 4,
                        "preco": 15.0,
                        "status_id": 7,
                        "media_num": 7.0,
                        "clube_nome": "Time Y",
                        "confronto": "Y x X",
                    },
                ]
            )

    class PositionDummyPredictionRepo:
        def get_previsoes(self):
            return pd.DataFrame(
                [
                    {"atleta_id": 1, "xp_previsto": 12.0},
                    {"atleta_id": 2, "xp_previsto": 6.5},
                ]
            )

    def fake_pontuados_by_rodada(rodada):
        return pd.DataFrame(
            [{"atleta_id": 1, "rodada": rodada, "pontos": 11.5}]
        )

    monkeypatch.setattr(
        "application.use_cases.get_retrospective_use_case.CartolaAPI.get_pontuados_by_rodada",
        fake_pontuados_by_rodada,
    )

    use_case = GetRetrospectiveUseCase(PositionDummyAthleteRepo(), PositionDummyPredictionRepo())
    df = use_case.execute(posicao_id=6, rodada=15)

    assert len(df) == 1
    assert df.iloc[0]["atleta_id"] == 1
    assert df.iloc[0]["rodada"] == 15
    assert df.iloc[0]["pontos_reais"] == 11.5
    assert df.iloc[0]["erro_absoluto"] == 0.5
