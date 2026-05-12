import pandas as pd

from core.optimizer import otimizar_escalacao


def test_otimizar_escalacao_retorna_11_jogadores_com_capitao():
    df = pd.DataFrame(
        [
            {"atleta_id": 1, "apelido": "A", "posicao_id": 1, "preco": 20.0, "status_id": 7, "xp_previsto": 10.0, "media_num": 8.0, "clube_nome": "X", "confronto":""},
            {"atleta_id": 2, "apelido": "B", "posicao_id": 2, "preco": 15.0, "status_id": 7, "xp_previsto": 9.0, "media_num": 7.0, "clube_nome": "Y", "confronto":""},
            {"atleta_id": 3, "apelido": "C", "posicao_id": 2, "preco": 12.0, "status_id": 7, "xp_previsto": 8.0, "media_num": 6.0, "clube_nome": "Z", "confronto":""},
            {"atleta_id": 4, "apelido": "D", "posicao_id": 3, "preco": 14.0, "status_id": 7, "xp_previsto": 7.5, "media_num": 6.5, "clube_nome": "X", "confronto":""},
            {"atleta_id": 5, "apelido": "E", "posicao_id": 3, "preco": 13.0, "status_id": 7, "xp_previsto": 7.0, "media_num": 6.0, "clube_nome": "Y", "confronto":""},
            {"atleta_id": 6, "apelido": "F", "posicao_id": 4, "preco": 11.0, "status_id": 7, "xp_previsto": 6.5, "media_num": 5.5, "clube_nome": "Z", "confronto":""},
            {"atleta_id": 7, "apelido": "G", "posicao_id": 4, "preco": 10.0, "status_id": 7, "xp_previsto": 6.0, "media_num": 5.0, "clube_nome": "X", "confronto":""},
            {"atleta_id": 8, "apelido": "H", "posicao_id": 4, "preco": 9.0, "status_id": 7, "xp_previsto": 5.5, "media_num": 4.5, "clube_nome": "Y", "confronto":""},
            {"atleta_id": 9, "apelido": "I", "posicao_id": 5, "preco": 19.0, "status_id": 7, "xp_previsto": 11.0, "media_num": 9.0, "clube_nome": "Z", "confronto":""},
            {"atleta_id": 10, "apelido": "J", "posicao_id": 5, "preco": 18.0, "status_id": 7, "xp_previsto": 10.5, "media_num": 8.5, "clube_nome": "X", "confronto":""},
            {"atleta_id": 11, "apelido": "K", "posicao_id": 6, "preco": 5.0, "status_id": 7, "xp_previsto": 2.0, "media_num": 3.0, "clube_nome": "Y", "confronto":""},
        ]
    )

    esquema = {1: 1, 2: 2, 3: 2, 4: 3, 5: 2, 6: 1}
    resultado = otimizar_escalacao(df, 120.0, esquema, "mito")

    assert not resultado.empty
    assert resultado.shape[0] == 11
    assert resultado[resultado["capitao"]].shape[0] == 1
    assert resultado[resultado["capitao"]]["apelido"].iloc[0] == "I"
