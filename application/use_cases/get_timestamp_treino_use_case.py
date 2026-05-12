from typing import Optional

from domain.repositories.prediction_repository import PredictionRepository


class GetTimestampTreinoUseCase:
    def __init__(self, prediction_repository: PredictionRepository):
        self.prediction_repository = prediction_repository

    def execute(self) -> Optional[str]:
        return self.prediction_repository.get_timestamp_treino()
