import streamlit as st
from streamlit.connections import BaseConnection
from supabase import create_client
import pandas as pd

class SupabaseDB(BaseConnection):
    """
    Conexão com Supabase para gerenciar dados do Cartola FC.
    Usa st.connection do Streamlit para integração.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Conectar ao Supabase usando secrets
        self.client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )

    def _connect(self, **kwargs):
        # Conexão já estabelecida no __init__
        pass

    def get_atletas_provaveis(self):
        """
        Busca atletas com status_id == 7 (Provável) da tabela 'atletas'.
        Retorna um DataFrame com as colunas definidas na seção 3 do MD.
        """
        response = self.client.table('atletas').select(
            'atleta_id, apelido, posicao_id, preco, status_id, media_num'
        ).eq('status_id', 7).execute()
        df_atletas = pd.DataFrame(response.data)
        
        # Buscar previsões
        df_preds = self.get_previsoes()
        
        # Fazer merge com previsões
        if not df_preds.empty:
            df = df_atletas.merge(df_preds, on='atleta_id', how='left')
        else:
            df = df_atletas.copy()
            df['xp_previsto'] = 0.0
        
        # Preencher NaN com 0
        df['xp_previsto'] = df['xp_previsto'].fillna(0.0)
        
        return df

    def save_previsao(self, atleta_id, xp_previsto):
        """
        Salva ou atualiza a previsão xp_previsto para um atleta na tabela 'previsoes'.
        """
        self.client.table('previsoes').upsert({
            'atleta_id': atleta_id,
            'xp_previsto': xp_previsto
        }).execute()

    def get_previsoes(self):
        """
        Busca todas as previsões da tabela 'previsoes'.
        Retorna um DataFrame com atleta_id, xp_previsto, risco_atleta, timestamp_treino.
        """
        response = self.client.table('previsoes').select('atleta_id, xp_previsto, risco_atleta, timestamp_treino').execute()
        df = pd.DataFrame(response.data)
        return df
    
    def get_timestamp_treino(self):
        """
        Busca o timestamp_treino mais recente da tabela 'previsoes'.
        """
        response = self.client.table('previsoes').select('timestamp_treino').order('timestamp_treino', desc=True).limit(1).execute()
        if response.data:
            return response.data[0]['timestamp_treino']
        return None
    
    def get_todos_atletas(self):
        """
        Busca TODOS os atletas (não apenas prováveis).
        Retorna um DataFrame com todos os jogadores do mercado.
        """
        response = self.client.table('atletas').select(
            'atleta_id, apelido, posicao_id, preco, status_id, media_num'
        ).execute()
        df_atletas = pd.DataFrame(response.data)
        
        # Buscar previsões
        df_preds = self.get_previsoes()
        
        # Fazer merge com previsões
        if not df_preds.empty:
            df = df_atletas.merge(df_preds, on='atleta_id', how='left')
        else:
            df = df_atletas.copy()
            df['xp_previsto'] = 0.0
        
        df['xp_previsto'] = df['xp_previsto'].fillna(0.0)
        return df

# Para usar: conn = st.connection("supabase_db", type=SupabaseDB)
# df = conn.get_atletas_provaveis()