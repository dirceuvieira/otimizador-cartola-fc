import pandas as pd

def otimizar_escalacao(df, verba, esquema_tatico, modo):
    """
    Otimiza a escalação do Cartola FC usando lógica de Knapsack gulosa.

    Args:
        df (pd.DataFrame): DataFrame com atletas prováveis, contendo colunas:
            - atleta_id, apelido, posicao_id, preco, status_id, xp_previsto, media_num
        verba (float): Orçamento total em Cartoletas.
        esquema_tatico (dict): Dicionário com posições e quantidades, ex: {1:1, 2:2, 3:2, 4:3, 5:3, 6:1}
        modo (str): 'mito' para maximizar xp_previsto, 'consistencia' para maximizar efficiency (media_num / preco)

    Returns:
        pd.DataFrame: DataFrame com os jogadores selecionados (11 titulares + 1 técnico).
    """
    # Assumir que df já está filtrado para status_id == 7 (prováveis)
    # Calcular score baseado no modo
    if modo == 'mito':
        df = df.copy()
        df['score'] = df['xp_previsto']
    elif modo == 'consistencia':
        df = df.copy()
        df['score'] = df['media_num'] / df['preco']
    else:
        raise ValueError("Modo deve ser 'mito' ou 'consistencia'")

    # Selecionar os N melhores para cada posição
    selecionados = []
    for pos, n in esquema_tatico.items():
        pos_df = df[df['posicao_id'] == pos].sort_values('score', ascending=False).head(n)
        selecionados.extend(pos_df.to_dict('records'))

    escalacao_df = pd.DataFrame(selecionados)

    # Verificar orçamento
    total_preco = escalacao_df['preco'].sum()
    if total_preco <= verba:
        # Após selecionar os 11 titulares, identificar o capitão
        jogadores = escalacao_df[escalacao_df['posicao_id'] != 6]  # Excluir técnico
        if not jogadores.empty:
            capitao_idx = jogadores['xp_previsto'].idxmax()
            escalacao_df['capitao'] = False
            escalacao_df.loc[capitao_idx, 'capitao'] = True
        return escalacao_df

    # Ajuste guloso se orçamento estourar
    # TODO: Migrar para PuLP na lógica de substituição gulosa para futura implementação de programação linear.
    escalacao_df = escalacao_df.sort_values('preco', ascending=False)
    for idx in escalacao_df.index:
        row = escalacao_df.loc[idx]
        # Candidatos: mesma posição, não selecionados, ordenados por score desc
        candidatos = df[
            (df['posicao_id'] == row['posicao_id']) &
            (~df['atleta_id'].isin(escalacao_df['atleta_id']))
        ].sort_values('score', ascending=False)

        for _, cand in candidatos.iterrows():
            novo_preco = total_preco - row['preco'] + cand['preco']
            if novo_preco <= verba:
                # Substituir
                escalacao_df.loc[idx] = cand
                total_preco = novo_preco
                break
        if total_preco <= verba:
            break

    # Após ajuste, identificar o capitão novamente
    jogadores = escalacao_df[escalacao_df['posicao_id'] != 6]
    if not jogadores.empty:
        capitao_idx = jogadores['xp_previsto'].idxmax()
        escalacao_df['capitao'] = False
        escalacao_df.loc[capitao_idx, 'capitao'] = True

    return escalacao_df