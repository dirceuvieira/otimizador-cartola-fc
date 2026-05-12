from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class PredictionRepository(ABC):
    @abstractmethod
    def get_previsoes(self) -> pd.DataFrame:
        """Retorna previsões disponíveis."""
        raise NotImplementedError

    @abstractmethod
    def get_timestamp_treino(self) -> Optional[str]:
        """Retorna o timestamp do último treino salvo."""
        raise NotImplementedError

    @abstractmethod
    def save_previsao(self, atleta_id: int, xp_previsto: float) -> None:
        """Salva ou atualiza a previsão de um atleta."""
        raise NotImplementedError

    @abstractmethod
    def save_predictions(self, df_preds: pd.DataFrame) -> None:
        """Salva ou atualiza previsões em lote."""
        raise NotImplementedError
