from pydantic import BaseModel
from typing import Dict, Any


class AtletaSchema(BaseModel):
    atleta_id: int
    apelido: str
    posicao_id: int
    preco: float
    status_id: int
    scouts: Dict[str, Any]  # Dicionário de scouts, pode ser vazio ou com chaves como 'G', 'A', etc.