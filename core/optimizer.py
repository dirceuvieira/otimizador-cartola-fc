import pandas as pd

from domain.entities.atleta import Atleta
from domain.services.escalacao_optimizer import EscalacaoOptimizer
from domain.value_objects.tactical_scheme import TacticalScheme


def _build_atletas_from_dataframe(df: pd.DataFrame) -> list[Atleta]:
    atletas = []
    for row in df.to_dict("records"):
        atletas.append(
            Atleta(
                atleta_id=int(row.get("atleta_id", 0)),
                apelido=str(row.get("apelido", "")),
                posicao_id=int(row.get("posicao_id", 0)),
                preco=float(row.get("preco", 0.0)),
                status_id=int(row.get("status_id", 0)),
                xp_previsto=float(row.get("xp_previsto", 0.0)),
                media_num=float(row.get("media_num", 0.0)),
                clube_nome=str(row.get("clube_nome", "")),
                confronto=str(row.get("confronto", "")),
            )
        )
    return atletas


def otimizar_escalacao(df, verba, esquema_tatico, modo):
    """
    Wrapper compatível que delega a lógica de otimização para o domínio.

    Continua aceitando a mesma API usada pela aplicação atual.
    """
    atletas = _build_atletas_from_dataframe(df)
    esquema = TacticalScheme(esquema_tatico)
    selecionados = EscalacaoOptimizer.optimize(atletas, verba, esquema, modo)

    if not selecionados:
        return pd.DataFrame([])

    return pd.DataFrame(
        [
            {
                "atleta_id": atleta.atleta_id,
                "apelido": atleta.apelido,
                "posicao_id": atleta.posicao_id,
                "preco": atleta.preco,
                "status_id": atleta.status_id,
                "xp_previsto": atleta.xp_previsto,
                "media_num": atleta.media_num,
                "clube_nome": atleta.clube_nome,
                "confronto": atleta.confronto,
                "capitao": atleta.capitao,
            }
            for atleta in selecionados
        ]
    )
