from copy import deepcopy
from typing import Iterable, List

from domain.entities.atleta import Atleta
from domain.value_objects.tactical_scheme import TacticalScheme


class EscalacaoOptimizer:
    @staticmethod
    def optimize(
        atletas: Iterable[Atleta],
        verba: float,
        esquema: TacticalScheme,
        modo: str,
    ) -> List[Atleta]:
        atletas = [deepcopy(atleta) for atleta in atletas]

        if modo == "mito":
            for atleta in atletas:
                atleta.score = atleta.xp_previsto
        elif modo == "consistencia":
            for atleta in atletas:
                atleta.score = atleta.media_num / atleta.preco if atleta.preco > 0 else 0.0
        else:
            raise ValueError("Modo deve ser 'mito' ou 'consistencia'")

        selecionados: List[Atleta] = []
        for posicao, quantidade in esquema.required_players().items():
            candidatos = [a for a in atletas if a.posicao_id == posicao]
            candidatos.sort(key=lambda atleta: atleta.score, reverse=True)
            selecionados.extend(candidatos[:quantidade])

        total_preco = sum(atleta.preco for atleta in selecionados)
        if total_preco <= verba:
            return EscalacaoOptimizer._apply_capitao(selecionados)

        selecionados = EscalacaoOptimizer._apply_budget_adjustment(
            atletas, selecionados, verba
        )
        return EscalacaoOptimizer._apply_capitao(selecionados)

    @staticmethod
    def _apply_budget_adjustment(
        todos_atletas: List[Atleta],
        selecionados: List[Atleta],
        verba: float,
    ) -> List[Atleta]:
        selecionados = [deepcopy(atleta) for atleta in selecionados]
        total_preco = sum(atleta.preco for atleta in selecionados)

        # Tentar reduzir custo trocando por atletas mais baratos da mesma posição
        selecionados.sort(key=lambda atleta: atleta.preco, reverse=True)
        for idx, atleta_atual in enumerate(selecionados):
            candidatos = [
                a
                for a in todos_atletas
                if a.posicao_id == atleta_atual.posicao_id
                and a.atleta_id != atleta_atual.atleta_id
                and a.atleta_id not in {s.atleta_id for s in selecionados}
            ]
            candidatos.sort(key=lambda atleta: atleta.score, reverse=True)
            for candidato in candidatos:
                novo_preco = total_preco - atleta_atual.preco + candidato.preco
                if novo_preco <= verba:
                    selecionados[idx] = candidato
                    total_preco = novo_preco
                    break
            if total_preco <= verba:
                break

        return selecionados

    @staticmethod
    def _apply_capitao(selecionados: List[Atleta]) -> List[Atleta]:
        for atleta in selecionados:
            atleta.capitao = False

        titulares = [a for a in selecionados if a.posicao_id != 6]
        if not titulares:
            return selecionados

        capitao = max(titulares, key=lambda atleta: atleta.xp_previsto)
        for atleta in selecionados:
            if atleta.atleta_id == capitao.atleta_id:
                atleta.capitao = True
                break

        return selecionados
