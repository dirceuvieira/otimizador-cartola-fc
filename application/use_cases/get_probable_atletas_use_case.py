import pandas as pd

from domain.repositories.athlete_repository import AthleteRepository


class GetProbableAtletasUseCase:
    def __init__(self, athlete_repository: AthleteRepository):
        self.athlete_repository = athlete_repository

    def execute(self) -> pd.DataFrame:
        """Retorna o DataFrame de atletas prováveis com previsões incorporadas."""
        return self.athlete_repository.get_probable_atletas()
