import streamlit as st
import pandas as pd
from datetime import datetime
from data.supabase_db import SupabaseDB
from core.optimizer import otimizar_escalacao

st.set_page_config(page_title="Cartola FC Optimizer", page_icon="⚽", layout="wide")
st.title("⚽ Otimizador Cartola FC - Estilo Brasfoot")

# Inicializar session state
if 'df_atletas' not in st.session_state:
    st.session_state['df_atletas'] = None
if 'last_sync' not in st.session_state:
    st.session_state['last_sync'] = None

# Sidebar com filtros
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Botão Sincronizar (sempre visível)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Sincronizar", use_container_width=True, help="Busca dados frescos do Supabase"):
            try:
                conn = st.connection("supabase_db", type=SupabaseDB)
                df_probables = conn.get_atletas_provaveis()
                st.session_state['df_atletas'] = df_probables
                st.session_state['last_sync'] = datetime.now()
                st.success(f"✅ Sincronizado! {len(df_probables)} atletas prováveis")
            except Exception as e:
                st.error(f"❌ Erro ao sincronizar: {e}")
    
    with col2:
        if st.button("📊 Mercado", use_container_width=True, help="Ver todos os atletas"):
            try:
                conn = st.connection("supabase_db", type=SupabaseDB)
                df_all = conn.get_todos_atletas()
                st.session_state['view_all'] = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro: {e}")
    
    # Mostrar último sync
    if st.session_state['last_sync']:
        st.caption(f"Última sincronização: {st.session_state['last_sync'].strftime('%H:%M:%S')}")
    
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
    df_display = df_display.sort_values('xp_previsto', ascending=False)
    
    st.dataframe(
        df_display[['apelido', 'posicao_id', 'preco', 'media_num', 'xp_previsto']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "apelido": st.column_config.TextColumn("🎯 Jogador"),
            "posicao_id": st.column_config.NumberColumn("📍 Posição"),
            "preco": st.column_config.NumberColumn("💰 Preço", format="R$ %.2f"),
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
                # Calcular totais
                total_custo = escalacao['preco'].sum()
                total_xp = escalacao['xp_previsto'].sum()
                gasto_percentual = (total_custo / verba) * 100
                
                # Exibir resumo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Custo Total", f"R$ {total_custo:.2f}", f"{gasto_percentual:.1f}% do orçamento")
                with col2:
                    st.metric("⭐ XP Total Previsto", f"{total_xp:.2f}")
                with col3:
                    st.metric("💵 Restante", f"R$ {verba - total_custo:.2f}")
                
                # Tabela de Escalação
                escalacao_display = escalacao.copy()
                st.dataframe(
                    escalacao_display[['apelido', 'posicao_id', 'preco', 'xp_previsto']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "apelido": st.column_config.TextColumn("🎯 Jogador"),
                        "posicao_id": st.column_config.NumberColumn("📍 Posição"),
                        "preco": st.column_config.NumberColumn("💰 Preço", format="R$ %.2f"),
                        "xp_previsto": st.column_config.NumberColumn("⭐ XP Previsto", format="%.2f")
                    }
                )
                
                # Botão para exportar
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