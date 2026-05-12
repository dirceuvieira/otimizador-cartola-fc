from abc import ABC, abstractmethod

import pandas as pd


class AthleteRepository(ABC):
    @abstractmethod
    def get_probable_atletas(self) -> pd.DataFrame:
        """Retorna os atletas prováveis com colunas esperadas pelo app."""
        raise NotImplementedError

    @abstractmethod
    def get_all_atletas(self) -> pd.DataFrame:
        """Retorna todos os atletas do mercado com colunas esperadas pelo app."""
        raise NotImplementedError
