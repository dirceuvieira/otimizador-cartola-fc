import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from adapters.supabase_repository import (
    SupabaseAthleteRepository,
    SupabasePredictionRepository,
)
from data.cartola_api import CartolaAPI
from application.use_cases.get_all_atletas_use_case import GetAllAtletasUseCase
from application.use_cases.get_probable_atletas_use_case import GetProbableAtletasUseCase
from application.use_cases.get_retrospective_use_case import GetRetrospectiveUseCase
from application.use_cases.get_timestamp_treino_use_case import GetTimestampTreinoUseCase
from core.optimizer import otimizar_escalacao

# Mapeamento de posição
POSICAO_MAP = {
    1: "1 - GOL",
    2: "2 - LAT",
    3: "3 - ZAG",
    4: "4 - MEI",
    5: "5 - ATA",
    6: "6 - TEC",
}

POSICAO_FILTERS = [
    ("Técnico", 6),
    ("Goleiros", 1),
    ("Laterais", 2),
    ("Zagueiros", 3),
    ("Meias", 4),
    ("Atacantes", 5),
    ("Todos", None),
]

def map_posicao(posicao_id):
    """Converte posicao_id para nome legível"""
    return POSICAO_MAP.get(int(posicao_id), str(posicao_id))

st.set_page_config(page_title="Cartola FC Optimizer", page_icon="⚽", layout="wide")
st.title("⚽ Mestre de Verdade - Cartola FC")

# Inicializar session state
if 'df_atletas' not in st.session_state:
    st.session_state['df_atletas'] = None
if 'df_retro' not in st.session_state:
    st.session_state['df_retro'] = None
if 'last_sync' not in st.session_state:
    st.session_state['last_sync'] = None
if 'timestamp_treino' not in st.session_state:
    st.session_state['timestamp_treino'] = None

# Sidebar com filtros
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Botão Sincronizar (sempre visível)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Sincronizar", use_container_width=True, help="Busca dados frescos do Supabase"):
            try:
                athlete_repo = SupabaseAthleteRepository()
                prediction_repo = SupabasePredictionRepository()
                get_probable_atletas = GetProbableAtletasUseCase(athlete_repo)
                get_timestamp_treino = GetTimestampTreinoUseCase(prediction_repo)

                df_probables = get_probable_atletas.execute()
                timestamp_treino = get_timestamp_treino.execute()

                st.session_state['df_atletas'] = df_probables
                st.session_state['last_sync'] = datetime.now()
                st.session_state['timestamp_treino'] = timestamp_treino
                st.success(f"✅ Sincronizado! {len(df_probables)} atletas prováveis")
            except Exception as e:
                st.error(f"❌ Erro ao sincronizar: {e}")
    
    with col2:
        if st.button("📊 Mercado", use_container_width=True, help="Ver todos os atletas"):
            try:
                athlete_repo = SupabaseAthleteRepository()
                get_all_atletas = GetAllAtletasUseCase(athlete_repo)
                df_all = get_all_atletas.execute()
                st.session_state['df_atletas'] = df_all
                st.session_state['view_all'] = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro: {e}")
    
    # Mostrar último sync
    if st.session_state['last_sync']:
        st.caption(f"Última sincronização: {st.session_state['last_sync'].strftime('%H:%M:%S')}")
    
    # Exibir timestamp_treino
    if st.session_state['timestamp_treino']:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(st.session_state['timestamp_treino'])
            st.caption(f"Dados treinados em: {dt.strftime('%d/%m/%Y %H:%M')}")
        except:
            st.caption(f"Dados treinados em: {st.session_state['timestamp_treino']}")
    
    st.divider()
    
    # Parâmetros de Otimização
    st.subheader("Parâmetros de Otimização")
    
    # Orçamento Total
    verba = st.slider("💰 Orçamento Total (Cartoletas)", min_value=50.0, max_value=200.0, value=100.0, step=1.0)

    # Esquema Tático
    esquemas = {
        "4-3-3": {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 1},
        "3-4-3": {1: 1, 2: 2, 3: 3, 4: 4, 5: 3, 6: 1},
        "4-4-2": {1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1},
        "3-5-2": {1: 1, 2: 2, 3: 3, 4: 5, 5: 2, 6: 1}
    }
    esquema_nome = st.selectbox("🎯 Esquema Tático", options=list(esquemas.keys()))
    esquema = esquemas[esquema_nome]

    # Estratégia da IA
    modo = st.radio("🤖 Estratégia da IA", options=["mito", "consistencia"], 
                    help="'Mito' = máximo xP; 'Consistência' = melhor relação performance/preço")

# Main Panel
tabs = st.tabs(["🏟️ Mercado Inteligente", "📈 Retrospectiva"])

with tabs[0]:
    st.header("🏟️ Mercado Inteligente")

    if st.session_state['df_atletas'] is not None and len(st.session_state['df_atletas']) > 0:
        df = st.session_state['df_atletas']
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Atletas Prováveis", len(df))
        with col2:
            st.metric("💰 Preço Médio", f"R$ {df['preco'].mean():.2f}")
        with col3:
            st.metric("⭐ XP Médio Previsto", f"{df['xp_previsto'].mean():.2f}")
        with col4:
            st.metric("📊 Posições", f"{df['posicao_id'].nunique()}")
        
        st.divider()
        
        # Tabela de Mercado
        st.markdown("**Todos os jogadores prováveis. Ordene clicando nos cabeçalhos.**")
        
        # Preparar dataframe para exibição
        df_display = df.copy()
        df_display['posicao_nome'] = df_display['posicao_id'].apply(map_posicao)
        df_display = df_display.sort_values('xp_previsto', ascending=False)
        
        st.dataframe(
            df_display[['apelido', 'clube_nome', 'posicao_nome', 'preco', 'media_num', 'xp_previsto']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "posicao_nome": st.column_config.TextColumn("📍 Posição"),
                "apelido": st.column_config.TextColumn("Atleta"),
                "clube_nome": st.column_config.TextColumn("Clube", width="small"),
                "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                "media_num": st.column_config.NumberColumn("📈 Média", format="%.2f"),
                "xp_previsto": st.column_config.NumberColumn("⭐ XP Previsto", format="%.2f")
            }
        )
        
        st.divider()
        
        # Escalação Recomendada
        st.header("⚽ Escalação Recomendada")
        
        if st.button("🎯 Otimizar Escalação", type="primary", use_container_width=True):
            try:
                escalacao = otimizar_escalacao(df, verba, esquema, modo)
                
                if escalacao.empty:
                    st.warning("⚠️ Nenhuma escalação válida encontrada com os parâmetros atuais.")
                else:
                    total_custo = escalacao['preco'].sum()
                    total_xp = escalacao['xp_previsto'].sum()
                    if 'capitao' in escalacao.columns and escalacao['capitao'].any():
                        capitao_xp = escalacao.loc[escalacao['capitao'], 'xp_previsto'].iloc[0]
                        total_xp += capitao_xp
                    gasto_percentual = (total_custo / verba) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Custo Total", f"R$ {total_custo:.2f}", f"{gasto_percentual:.1f}% do orçamento")
                    with col2:
                        st.metric("⭐ XP Total Previsto", f"{total_xp:.2f}")
                    with col3:
                        st.metric("💵 Restante", f"R$ {verba - total_custo:.2f}")
                    
                    escalacao_display = escalacao.copy()
                    escalacao_display['posicao_nome'] = escalacao_display['posicao_id'].apply(map_posicao)
                    escalacao_display['capitao_emoji'] = escalacao_display['capitao'].apply(lambda x: '⭐' if x else '')
                    st.dataframe(
                        escalacao_display[['capitao_emoji', 'apelido', 'clube_nome', 'posicao_nome', 'preco', 'xp_previsto']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "capitao_emoji": st.column_config.TextColumn("Capitão"),
                            "posicao_nome": st.column_config.TextColumn("📍 Posição"),
                            "apelido": st.column_config.TextColumn("Atleta"),
                            "clube_nome": st.column_config.TextColumn("Clube", width="small"),
                            "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                            "xp_previsto": st.column_config.NumberColumn("⭐ XP Previsto", format="%.2f")
                        }
                    )
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**💰 Custo Total:** R$ {total_custo:.2f}")
                    with col2:
                        st.markdown(f"**⭐ XP Total (com Capitão):** {total_xp:.2f}")
                    
                    csv = escalacao_display.to_csv(index=False)
                    st.download_button(
                        label="📥 Baixar Escalação (CSV)",
                        data=csv,
                        file_name=f"escalacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
            except Exception as e:
                st.error(f"❌ Erro na otimização: {str(e)}")

    else:
        st.info("📡 Clique em '🔄 Sincronizar' na sidebar para carregar os dados e começar a otimizar!")

with tabs[1]:
    st.header("📈 Retrospectiva de Previsões")
    st.write("Compare as previsões salvas em Supabase com os resultados reais do Cartola.")

    st.subheader("Filtros de Retrospectiva")
    posicao_labels = [label for label, _ in POSICAO_FILTERS]
    posicao_selecionada = st.selectbox("Filtrar por posição", posicao_labels, index=0)
    posicao_id = dict(POSICAO_FILTERS)[posicao_selecionada]

    rodada_atual = None
    try:
        rodada_atual = CartolaAPI.get_rodada_atual()
    except Exception:
        rodada_atual = None

    if rodada_atual is not None:
        rodada = st.number_input(
            "Rodada",
            min_value=1,
            max_value=rodada_atual,
            value=rodada_atual,
            step=1,
            help="Escolha a rodada para buscar os atletas pontuados.",
        )
        st.caption(f"Rodada atual disponível: {rodada_atual}")
    else:
        rodada = st.number_input(
            "Rodada",
            min_value=1,
            value=1,
            step=1,
            help="Não foi possível obter a rodada atual da API. Informe manualmente.",
        )

    if st.button("🔄 Atualizar Retrospectiva", use_container_width=True):
        try:
            athlete_repo = SupabaseAthleteRepository()
            prediction_repo = SupabasePredictionRepository()
            get_retrospective = GetRetrospectiveUseCase(athlete_repo, prediction_repo)
            df_retro = get_retrospective.execute(posicao_id=posicao_id, rodada=int(rodada))
            st.session_state['df_retro'] = df_retro
            st.success(f"✅ Retrospectiva atualizada com {len(df_retro)} atletas")
        except Exception as e:
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}"
            with st.expander("❌ Detalhes do erro", expanded=False):
                st.code(traceback.format_exc(), language="text")
            st.error(f"❌ Erro ao atualizar retrospectiva: {error_details}")

    if st.session_state['df_retro'] is not None and len(st.session_state['df_retro']) > 0:
        df_retro = st.session_state['df_retro'].copy()
        df_retro['posicao_nome'] = df_retro['posicao_id'].apply(map_posicao)
        df_retro['erro_pct'] = df_retro['erro_pct'].fillna(0.0)

        mae = df_retro['erro_absoluto'].mean()
        rmse = (df_retro['erro_assinado'] ** 2).mean() ** 0.5
        bias = df_retro['erro_assinado'].mean()
        filled_count = int(df_retro['pontos_reais'].notna().sum())
        total_count = len(df_retro)

        with st.expander("Métricas de calibragem", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("MAE", f"{mae:.2f}")
            with col2:
                st.metric("RMSE", f"{rmse:.2f}")
            with col3:
                st.metric("Bias", f"{bias:.2f}")
            with col4:
                st.metric("Atletas com resultado", f"{filled_count}/{total_count}")

        st.divider()
        st.dataframe(
            df_retro[
                [
                    'apelido',
                    'clube_nome',
                    'posicao_nome',
                    'status_id',
                    'xp_previsto',
                    'pontos_reais',
                    'erro_absoluto',
                    'erro_assinado',
                    'erro_pct',
                    'rodada',
                ]
            ].sort_values('erro_absoluto', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                'posicao_nome': st.column_config.TextColumn('📍 Posição'),
                'apelido': st.column_config.TextColumn('Atleta'),
                'clube_nome': st.column_config.TextColumn('Clube', width='small'),
                'preco': st.column_config.NumberColumn('Preço', format='R$ %.2f') if 'preco' in df_retro.columns else None,
                'xp_previsto': st.column_config.NumberColumn('⭐ XP Previsto', format='%.2f'),
                'pontos_reais': st.column_config.NumberColumn('📌 Pontos Reais', format='%.2f'),
                'erro_absoluto': st.column_config.NumberColumn('Erro Absoluto', format='%.2f'),
                'erro_assinado': st.column_config.NumberColumn('Erro Assinado', format='%.2f'),
                'erro_pct': st.column_config.NumberColumn('Erro %', format='%.2f'),
                'rodada': st.column_config.NumberColumn('Rodada'),
            }
        )

        csv = df_retro.to_csv(index=False)
        st.download_button(
            label="📥 Baixar Retrospectiva (CSV)",
            data=csv,
            file_name=f"retrospectiva_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Clique em '🔄 Atualizar Retrospectiva' para comparar previsões com resultados reais.")
