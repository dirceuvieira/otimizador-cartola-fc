from dataclasses import dataclass, field
from typing import Any

@dataclass
class Atleta:
    atleta_id: int
    apelido: str
    posicao_id: int
    preco: float
    status_id: int = 0
    xp_previsto: float = 0.0
    media_num: float = 0.0
    clube_nome: str = ""
    confronto: str = ""
    capitao: bool = False
    score: float = field(default=0.0, compare=False)

    def with_score(self, score: float) -> "Atleta":
        return Atleta(
            atleta_id=self.atleta_id,
            apelido=self.apelido,
            posicao_id=self.posicao_id,
            preco=self.preco,
            status_id=self.status_id,
            xp_previsto=self.xp_previsto,
            media_num=self.media_num,
            clube_nome=self.clube_nome,
            confronto=self.confronto,
            capitao=self.capitao,
            score=score,
        )
