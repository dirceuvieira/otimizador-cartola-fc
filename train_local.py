import os
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
import joblib
from supabase import create_client
from data.cartola_api import CartolaAPI
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "modelo_rodada_atual.pkl"


def log(message: str) -> None:
    print(f"[INFO] {message}")


def load_csv(filename: str) -> pd.DataFrame:
    """Carrega CSV local se disponível."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return pd.read_csv(path)


def load_csv_or_none(filename: str) -> pd.DataFrame | None:
    """Tenta carregar CSV local; retorna None se não encontrado."""
    try:
        return load_csv(filename)
    except FileNotFoundError:
        return None


def load_mercado_data() -> pd.DataFrame:
    """Carrega dados do mercado via API ou fallback local."""
    try:
        log("Buscando dados do mercado via API do Cartola FC")
        return CartolaAPI.get_mercado_data()
    except Exception as e:
        log(f"Falha na API: {e}. Tentando carregar CSV local...")
        return load_csv("mercado_atual.csv")


def download_and_save_historico() -> pd.DataFrame:
    """
    Baixa dados do mercado via CartolaAPI e processa para gerar histórico inicial.
    Salva como historico_scouts.csv para uso futuro.
    
    Retorna:
        pd.DataFrame: DataFrame com colunas de histórico (atleta_id, posicao_id, preco, pontos, casa, etc.)
    """
    log("Arquivo historico_scouts.csv não encontrado. Baixando dados via API...")
    try:
        df_market = CartolaAPI.get_mercado_data()
        log(f"Mercado baixado: {len(df_market)} atletas")
        
        # Preparar dados iniciais com scouts como base do histórico
        base_cols = ["atleta_id", "apelido", "posicao_id", "preco", "status_id", "media_num"]
        extra_cols = ["clube_id", "clube_nome", "rodada_id"]
        
        cols_to_select = [col for col in base_cols + extra_cols if col in df_market.columns]
        df_hist = df_market[cols_to_select].copy()
        
        # Adicionar colunas de scouts se existirem
        scout_cols = [col for col in df_market.columns if col.startswith("scout_")]
        for col in scout_cols:
            df_hist[col] = df_market[col]
        
        # Adicionar colunas de contexto
        df_hist["pontos"] = df_hist["media_num"]  # Usar média como estimativa de pontos
        df_hist["jogo_id"] = range(1, len(df_hist) + 1)
        if "rodada_id" not in df_hist.columns or df_hist["rodada_id"].isna().all():
            df_hist["rodada"] = 1
        else:
            df_hist["rodada"] = df_hist["rodada_id"]
        df_hist["casa"] = 1  # Assumir como padrão
        
        # Garantir que clube_id existe
        if "clube_id" not in df_hist.columns:
            df_hist["clube_id"] = 0
        
        # Salvar CSV
        csv_path = DATA_DIR / "historico_scouts.csv"
        df_hist.to_csv(csv_path, index=False)
        log(f"Histórico inicial salvo em {csv_path}")
        
        return df_hist
        
    except Exception as e:
        log(f"Falha ao baixar via API: {e}. Tentando usar arquivo de exemplo...")
        exemplo_path = DATA_DIR / "historico_scouts_exemplo.csv"
        if exemplo_path.exists():
            log(f"Usando arquivo de exemplo: {exemplo_path}")
            return pd.read_csv(exemplo_path)
        raise RuntimeError(f"Erro ao baixar dados e arquivo de exemplo não encontrado: {e}")


def infer_mando_campo(df: pd.DataFrame) -> pd.Series:
    if "casa" in df.columns:
        return df["casa"].astype(int).fillna(0)
    if "em_casa" in df.columns:
        return df["em_casa"].astype(int).fillna(0)
    if "mandante" in df.columns and "time" in df.columns:
        return (df["mandante"] == df["time"]).astype(int).fillna(0)
    if "local" in df.columns:
        return df["local"].astype(str).str.lower().isin(["casa", "home"]).astype(int)
    return pd.Series(0, index=df.index)


def get_round_column(df: pd.DataFrame) -> Optional[str]:
    for col in ("rodada", "rodada_id"):
        if col in df.columns:
            return col
    return None


def build_team_position_avg(df_hist: pd.DataFrame, last_n_rounds: int = 3) -> pd.DataFrame:
    round_col = get_round_column(df_hist)
    if round_col is None or "clube_id" not in df_hist.columns or "posicao_id" not in df_hist.columns:
        return pd.DataFrame(columns=["opponent_clube_id", "posicao_id", "scouts_cedidos_adv"])

    hist = df_hist.copy()
    hist[round_col] = pd.to_numeric(hist[round_col], errors="coerce").fillna(0).astype(int)
    hist = hist.dropna(subset=["clube_id", "posicao_id", "pontos"])
    hist["clube_id"] = hist["clube_id"].astype(int)
    hist["posicao_id"] = hist["posicao_id"].astype(int)
    hist["pontos"] = pd.to_numeric(hist["pontos"], errors="coerce").fillna(0)

    last_round = int(hist[round_col].max())
    recent = hist[hist[round_col] > last_round - last_n_rounds]
    avg = (
        recent.groupby(["clube_id", "posicao_id"], as_index=False)["pontos"]
        .mean()
        .rename(columns={"clube_id": "opponent_clube_id", "pontos": "scouts_cedidos_adv"})
    )
    return avg


def build_team_home_strength(df_hist: pd.DataFrame) -> pd.DataFrame:
    if "clube_id" not in df_hist.columns or "casa" not in df_hist.columns or "pontos" not in df_hist.columns:
        return pd.DataFrame(columns=["clube_id", "forca_mandante"])

    hist = df_hist.copy()
    hist["clube_id"] = pd.to_numeric(hist["clube_id"], errors="coerce").fillna(0).astype(int)
    hist["casa"] = pd.to_numeric(hist["casa"], errors="coerce").fillna(0).astype(int)
    hist["pontos"] = pd.to_numeric(hist["pontos"], errors="coerce").fillna(0)

    home_stats = hist[hist["casa"] == 1].groupby("clube_id")["pontos"].mean().reset_index(name="home_media")
    overall_stats = hist.groupby("clube_id")["pontos"].mean().reset_index(name="media_geral")
    strength = home_stats.merge(overall_stats, on="clube_id", how="left")
    strength["forca_mandante"] = strength["home_media"] / (strength["media_geral"].replace(0, 0.1))
    strength["forca_mandante"] = strength["forca_mandante"].fillna(1.0)
    return strength[["clube_id", "forca_mandante"]]


def assign_opponent_club(df_market: pd.DataFrame, df_partidas: pd.DataFrame) -> pd.DataFrame:
    if "clube_id" not in df_market.columns or df_partidas is None or df_partidas.empty:
        df_market = df_market.copy()
        df_market["adversario_clube_id"] = 0
        df_market["casa"] = infer_mando_campo(df_market)
        return df_market

    part_home = df_partidas[["time_casa_id", "time_visitante_id"]].rename(
        columns={"time_casa_id": "clube_id", "time_visitante_id": "adversario_clube_id"}
    )
    part_home["casa"] = 1
    part_away = df_partidas[["time_visitante_id", "time_casa_id"]].rename(
        columns={"time_visitante_id": "clube_id", "time_casa_id": "adversario_clube_id"}
    )
    part_away["casa"] = 0
    mapping = pd.concat([part_home, part_away], ignore_index=True)

    df_market = df_market.copy()
    df_market = df_market.merge(mapping, on="clube_id", how="left")
    df_market["adversario_clube_id"] = pd.to_numeric(df_market["adversario_clube_id"], errors="coerce").fillna(0).astype(int)
    df_market["casa"] = pd.to_numeric(df_market["casa"], errors="coerce").fillna(0).astype(int)
    return df_market


def compute_finalizacoes_acumuladas(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    df = safe_sort(df)
    for col in ["scout_FF", "scout_FS", "scout_FD"]:
        if col not in df.columns:
            df[col] = 0.0
    if "atleta_id" in df.columns:
        rolling = df.groupby("atleta_id")[["scout_FF", "scout_FS", "scout_FD"]].rolling(window=3, min_periods=1).sum()
        roll_sum = rolling.sum(axis=1).reset_index(level=0, drop=True)
        return roll_sum.shift(1).fillna(0)
    return pd.Series(0.0, index=df.index)


def add_engineered_features(df: pd.DataFrame, df_hist: pd.DataFrame, df_partidas: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    df = df.copy()
    
    # Garantir que pontos existe e é numérico
    if "pontos" not in df.columns:
        df["pontos"] = 0
    df["pontos"] = pd.to_numeric(df["pontos"], errors="coerce").fillna(0)
    
    # Garantir que clube_id existe
    if "clube_id" not in df.columns:
        df["clube_id"] = 0
    
    df = assign_opponent_club(df, df_partidas)

    team_position_avg = build_team_position_avg(df_hist)
    if not team_position_avg.empty:
        df = df.merge(
            team_position_avg,
            left_on=["adversario_clube_id", "posicao_id"],
            right_on=["opponent_clube_id", "posicao_id"],
            how="left",
        )
    if "scouts_cedidos_adv" not in df.columns:
        df["scouts_cedidos_adv"] = 0.0
    df["scouts_cedidos_adv"] = pd.to_numeric(df["scouts_cedidos_adv"], errors="coerce").fillna(0.0)

    home_strength = build_team_home_strength(df_hist)
    if not home_strength.empty and "clube_id" in df.columns:
        df = df.merge(home_strength, on="clube_id", how="left")
    if "forca_mandante" not in df.columns:
        df["forca_mandante"] = 1.0
    df["forca_mandante"] = pd.to_numeric(df["forca_mandante"], errors="coerce").fillna(1.0)

    finalizacoes_hist = df_hist.copy()
    finalizacoes_hist["finalizacoes_acumuladas"] = compute_finalizacoes_acumuladas(finalizacoes_hist)
    last_finalizacoes = finalizacoes_hist.groupby("atleta_id", as_index=False)["finalizacoes_acumuladas"].last()
    if not last_finalizacoes.empty:
        df = df.merge(last_finalizacoes, on="atleta_id", how="left")
    if "finalizacoes_acumuladas" not in df.columns:
        df["finalizacoes_acumuladas"] = 0.0
    df["finalizacoes_acumuladas"] = pd.to_numeric(df["finalizacoes_acumuladas"], errors="coerce").fillna(0.0)
    return df


def safe_sort(df: pd.DataFrame) -> pd.DataFrame:
    if "data" in df.columns:
        df = df.assign(data=pd.to_datetime(df["data"], errors="coerce"))
        return df.sort_values(["atleta_id", "data"])
    if "jogo_id" in df.columns:
        return df.sort_values(["atleta_id", "jogo_id"])
    return df.sort_values(["atleta_id"])


def compute_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pontos"] = df["pontos"].fillna(0)
    df = safe_sort(df)
    df["mando_campo"] = infer_mando_campo(df)

    # Garantir que clube_id é preservado
    if "clube_id" not in df.columns:
        df["clube_id"] = 0

    rolled = df.groupby("atleta_id")["pontos"].rolling(window=5, min_periods=1)
    media_movel = rolled.mean().reset_index(level=0, drop=True)
    indice_risco = rolled.std(ddof=0).fillna(0).reset_index(level=0, drop=True)

    df["media_movel"] = media_movel.shift(1)
    df["indice_risco"] = indice_risco.shift(1).fillna(0)
    return df


def prepare_training_data(df_hist: pd.DataFrame) -> pd.DataFrame:
    df = compute_rolling_features(df_hist)
    df = add_engineered_features(df, df_hist)
    required = [
        "media_movel",
        "indice_risco",
        "preco",
        "posicao_id",
        "mando_campo",
        "pontos",
        "scouts_cedidos_adv",
        "forca_mandante",
        "finalizacoes_acumuladas",
    ]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no histórico: {col}")

    df = df.dropna(subset=["media_movel"])
    df["preco"] = pd.to_numeric(df["preco"], errors="coerce").fillna(0)
    df["posicao_id"] = pd.to_numeric(df["posicao_id"], errors="coerce").fillna(0).astype(int)
    df["mando_campo"] = pd.to_numeric(df["mando_campo"], errors="coerce").fillna(0).astype(int)
    df["media_movel"] = df["media_movel"].fillna(0)
    df["indice_risco"] = df["indice_risco"].fillna(0)
    df["pontos"] = pd.to_numeric(df["pontos"], errors="coerce").fillna(0)
    df["scouts_cedidos_adv"] = pd.to_numeric(df["scouts_cedidos_adv"], errors="coerce").fillna(0)
    df["forca_mandante"] = pd.to_numeric(df["forca_mandante"], errors="coerce").fillna(1.0)
    df["finalizacoes_acumuladas"] = pd.to_numeric(df["finalizacoes_acumuladas"], errors="coerce").fillna(0)
    return df


def build_prediction_dataset(df_hist: pd.DataFrame, df_market: pd.DataFrame, df_partidas: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    df_hist = df_hist.copy()
    if "atleta_id" not in df_hist.columns:
        raise ValueError("Historico precisa conter atleta_id")
    
    # Agrupar por atleta_id e calcular média móvel e consistência
    df_hist["pontos"] = pd.to_numeric(df_hist["pontos"], errors="coerce").fillna(0)
    
    history_features_list = []
    for atleta_id in df_hist["atleta_id"].unique():
        pontos = df_hist[df_hist["atleta_id"] == atleta_id]["pontos"]
        media_movel = pontos.tail(5).mean()
        indice_risco = pontos.tail(5).std(ddof=0) if len(pontos.tail(5)) > 1 else 0
        
        history_features_list.append({
            "atleta_id": atleta_id,
            "media_movel": media_movel,
            "indice_risco": indice_risco if not pd.isna(indice_risco) else 0,
        })
    
    history_features = pd.DataFrame(history_features_list)

    df_market = df_market.copy()
    for col in ["preco", "posicao_id", "status_id"]:
        if col not in df_market.columns:
            raise ValueError(f"Mercado atual precisa conter {col}")

    df_market["preco"] = pd.to_numeric(df_market["preco"], errors="coerce").fillna(0)
    df_market["posicao_id"] = pd.to_numeric(df_market["posicao_id"], errors="coerce").fillna(0).astype(int)
    df_market["status_id"] = pd.to_numeric(df_market["status_id"], errors="coerce").fillna(0).astype(int)
    df_market["mando_campo"] = infer_mando_campo(df_market)

    df_market = add_engineered_features(df_market, df_hist, df_partidas)

    df = df_market.merge(history_features, how="left", on="atleta_id")
    df["media_movel"] = df["media_movel"].fillna(0)
    df["indice_risco"] = df["indice_risco"].fillna(0)
    return df


def train_model(df_train: pd.DataFrame) -> RandomForestRegressor:
    feature_cols = [
        "media_movel",
        "indice_risco",
        "preco",
        "posicao_id",
        "mando_campo",
        "scouts_cedidos_adv",
        "forca_mandante",
        "finalizacoes_acumuladas",
    ]
    X = df_train[feature_cols].astype(float)
    y = df_train["pontos"].astype(float)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


def create_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")
    return create_client(url, key)


def upsert_athletes(client, df_market: pd.DataFrame) -> None:
    """Salva dados dos atletas do mercado na tabela atletas"""
    # Selecionar e preparar colunas necessárias
    cols_to_upsert = ["atleta_id", "apelido", "posicao_id", "preco", "status_id", "media_num"]
    
    # Verificar se todas as colunas existem
    existing_cols = [col for col in cols_to_upsert if col in df_market.columns]
    df_athletes = df_market[existing_cols].copy()
    
    # Converter tipos de dados
    df_athletes["atleta_id"] = df_athletes["atleta_id"].astype(int)
    df_athletes["posicao_id"] = df_athletes["posicao_id"].astype(int)
    df_athletes["status_id"] = df_athletes["status_id"].astype(int)
    df_athletes["preco"] = pd.to_numeric(df_athletes["preco"], errors="coerce").fillna(0)
    df_athletes["media_num"] = pd.to_numeric(df_athletes["media_num"], errors="coerce").fillna(0)
    
    # Converter para lista de dicts
    payload = df_athletes.to_dict(orient="records")
    
    # Fazer upsert em lotes (Supabase tem limite de requisição)
    batch_size = 1000
    for i in range(0, len(payload), batch_size):
        batch = payload[i:i + batch_size]
        client.table("atletas").upsert(batch).execute()
        log(f"Upsert de atletas: {min(i + batch_size, len(payload))}/{len(payload)}")


def upsert_predictions(client, df_preds: pd.DataFrame) -> None:
    """Salva previsões na tabela previsoes"""
    timestamp_treino = datetime.now().isoformat()
    df_preds["risco_atleta"] = df_preds["indice_risco"]
    df_preds["timestamp_treino"] = timestamp_treino
    payload = df_preds[["atleta_id", "xp_previsto", "risco_atleta", "timestamp_treino"]].to_dict(orient="records")
    client.table("previsoes").upsert(payload).execute()


def save_model(model) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)


def main():
    log("Iniciando pipeline de treinamento local")

    log("Carregando dados históricos")
    df_hist = load_csv_or_none("historico_scouts.csv")
    
    if df_hist is None:
        log("Histórico não encontrado localmente. Iniciando download via API...")
        df_hist = download_and_save_historico()
    
    log("Carregando dados do mercado atual")
    df_market = load_mercado_data()
    log("Carregando partidas da rodada atual")
    df_partidas = CartolaAPI.get_partidas()

    log("Normalizando dados e preenchendo valores nulos")
    df_hist = df_hist.fillna(0)
    df_market = df_market.fillna(0)

    log("Preparando dados de treinamento")
    df_train = prepare_training_data(df_hist)
    if df_train.empty:
        raise ValueError("Dados insuficientes para treinar o modelo")

    log("Treinando RandomForestRegressor")
    model = train_model(df_train)
    save_model(model)
    log(f"Modelo salvo em {MODEL_PATH}")

    log("Construindo dataset de predição para atletas prováveis")
    df_predict = build_prediction_dataset(df_hist, df_market, df_partidas)
    df_probables = df_predict[df_predict["status_id"] == 7].copy()
    if df_probables.empty:
        log("Nenhum atleta provável encontrado para predição")
        return

    log("Gerando xp_previsto para atletas prováveis")
    feature_cols = [
        "media_movel",
        "indice_risco",
        "preco",
        "posicao_id",
        "mando_campo",
        "scouts_cedidos_adv",
        "forca_mandante",
        "finalizacoes_acumuladas",
    ]
    df_probables["xp_previsto"] = model.predict(df_probables[feature_cols].astype(float))

    log("Persistindo dados no Supabase")
    client = create_supabase_client()
    
    # Salvar atletas do mercado
    log("Salvando dados dos atletas na tabela 'atletas'")
    upsert_athletes(client, df_market)
    
    # Salvar previsões
    log("Salvando previsões na tabela 'previsoes'")
    upsert_predictions(client, df_probables)

    log("Treinamento local concluído com sucesso")


if __name__ == "__main__":
    main()
