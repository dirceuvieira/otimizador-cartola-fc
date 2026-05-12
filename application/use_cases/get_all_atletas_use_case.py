import pandas as pd

from domain.repositories.athlete_repository import AthleteRepository


class GetAllAtletasUseCase:
    def __init__(self, athlete_repository: AthleteRepository):
        self.athlete_repository = athlete_repository

    def execute(self) -> pd.DataFrame:
        """Retorna o DataFrame de todos os atletas do mercado, com previsões incorporadas."""
        return self.athlete_repository.get_all_atletas()
