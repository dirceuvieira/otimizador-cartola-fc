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
        """Treina o modelo e persiste atletas, previsões e features de matchup no repositório."""
        df_hist = training_helpers.load_csv_or_none("historico_scouts.csv")
        if df_hist is None:
            df_hist = training_helpers.download_and_save_historico()

        df_market = training_helpers.load_mercado_data()
        df_partidas = training_helpers.CartolaAPI.get_partidas()

        df_hist = df_hist.fillna(0)
        df_market = df_market.fillna(0)

        df_train = training_helpers.prepare_training_data(df_hist, df_partidas)
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
            "defesa_adversaria",
            "ataque_adversario",
            "finalizacoes_sofridas_adv",
        ]
        df_probables["xp_previsto"] = model.predict(df_probables[feature_cols].astype(float))

        self.athlete_repository.upsert_athletes(df_market)
        self.prediction_repository.save_predictions(df_probables)

        # Persist matchup features to database
        try:
            # Determine current rodada (extract from df_partidas or use default)
            rodada = int(df_partidas['rodada'].max()) if 'rodada' in df_partidas.columns and not df_partidas.empty else 1
            
            # Prepare features dataframe with required columns
            df_features = df_probables[[
                "atleta_id", 
                "adversario_clube_id", 
                "defesa_adversaria", 
                "ataque_adversario", 
                "finalizacoes_sofridas_adv"
            ]].copy()
            df_features["rodada"] = rodada
            df_features["timestamp_criacao"] = pd.Timestamp.now().isoformat()
            
            # Upsert matchup features
            self.prediction_repository.upsert_matchup_features(df_features)
            
            # Log training execution
            total_features = len(df_features)
            total_atletas = len(df_probables)
            self.prediction_repository.log_training_execution(
                rodada=rodada,
                total_atletas=total_atletas,
                total_features=total_features,
                status="success"
            )
        except Exception as e:
            # Log error but don't crash training
            try:
                rodada = int(df_partidas['rodada'].max()) if 'rodada' in df_partidas.columns and not df_partidas.empty else 1
                self.prediction_repository.log_training_execution(
                    rodada=rodada,
                    total_atletas=len(df_probables),
                    total_features=0,
                    status="error",
                    error_msg=str(e)
                )
            except Exception:
                pass
            print(f"[WARN] Erro ao persistir features de matchup: {e}")

        return model, df_probables
