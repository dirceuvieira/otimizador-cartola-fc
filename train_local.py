import os
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
import joblib
from supabase import create_client
from data.cartola_api import CartolaAPI

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
        df_hist = df_market[[
            "atleta_id", "apelido", "posicao_id", "preco", "status_id", "media_num"
        ]].copy()
        
        # Adicionar colunas de scouts se existirem
        scout_cols = [col for col in df_market.columns if col.startswith("scout_")]
        for col in scout_cols:
            df_hist[col] = df_market[col]
        
        # Adicionar colunas de contexto
        df_hist["pontos"] = df_hist["media_num"]  # Usar média como estimativa de pontos
        df_hist["jogo_id"] = range(1, len(df_hist) + 1)
        df_hist["rodada"] = 1
        df_hist["casa"] = 1  # Assumir como padrão
        
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

    rolled = df.groupby("atleta_id")["pontos"].rolling(window=5, min_periods=1)
    media_movel = rolled.mean().reset_index(level=0, drop=True)
    consistencia = rolled.std(ddof=0).fillna(0).reset_index(level=0, drop=True)

    df["media_movel"] = media_movel.shift(1)
    df["consistencia"] = consistencia.shift(1).fillna(0)
    return df


def prepare_training_data(df_hist: pd.DataFrame) -> pd.DataFrame:
    df = compute_rolling_features(df_hist)
    required = ["media_movel", "consistencia", "preco", "posicao_id", "mando_campo", "pontos"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no histórico: {col}")

    df = df.dropna(subset=["media_movel"])
    df["preco"] = pd.to_numeric(df["preco"], errors="coerce").fillna(0)
    df["posicao_id"] = pd.to_numeric(df["posicao_id"], errors="coerce").fillna(0).astype(int)
    df["mando_campo"] = pd.to_numeric(df["mando_campo"], errors="coerce").fillna(0).astype(int)
    df["media_movel"] = df["media_movel"].fillna(0)
    df["consistencia"] = df["consistencia"].fillna(0)
    df["pontos"] = pd.to_numeric(df["pontos"], errors="coerce").fillna(0)
    return df


def build_prediction_dataset(df_hist: pd.DataFrame, df_market: pd.DataFrame) -> pd.DataFrame:
    df_hist = df_hist.copy()
    if "atleta_id" not in df_hist.columns:
        raise ValueError("Historico precisa conter atleta_id")
    
    # Agrupar por atleta_id e calcular média móvel e consistência
    df_hist["pontos"] = pd.to_numeric(df_hist["pontos"], errors="coerce").fillna(0)
    
    history_features_list = []
    for atleta_id in df_hist["atleta_id"].unique():
        pontos = df_hist[df_hist["atleta_id"] == atleta_id]["pontos"]
        media_movel = pontos.tail(5).mean()
        consistencia = pontos.tail(5).std(ddof=0) if len(pontos.tail(5)) > 1 else 0
        
        history_features_list.append({
            "atleta_id": atleta_id,
            "media_movel": media_movel,
            "consistencia": consistencia if not pd.isna(consistencia) else 0,
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

    df = df_market.merge(history_features, how="left", on="atleta_id")
    df["media_movel"] = df["media_movel"].fillna(0)
    df["consistencia"] = df["consistencia"].fillna(0)
    return df


def train_model(df_train: pd.DataFrame) -> RandomForestRegressor:
    feature_cols = ["media_movel", "preco", "posicao_id", "mando_campo"]
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
    payload = df_preds[["atleta_id", "xp_previsto"]].to_dict(orient="records")
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
    df_predict = build_prediction_dataset(df_hist, df_market)
    df_probables = df_predict[df_predict["status_id"] == 7].copy()
    if df_probables.empty:
        log("Nenhum atleta provável encontrado para predição")
        return

    log("Gerando xp_previsto para atletas prováveis")
    feature_cols = ["media_movel", "preco", "posicao_id", "mando_campo"]
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
