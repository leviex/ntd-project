import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard NTD - Gestão de Projetos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 14px;
        color: #666;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Dashboard de Gestão de Projetos NTD")
st.markdown("---")

# Função para carregar dados
@st.cache_data
def carregar_dados():
    """Carrega dados do arquivo CSV"""
    try:
        df = pd.read_csv('Roadmap_Projetos_NTD.csv')
        df.columns = df.columns.str.strip()
        # Processamento de datas
        df['Previsão de Entrega'] = pd.to_datetime(df['Previsão de Entrega'], format='%d/%m/%Y', errors='coerce')
        
        # Cálculo de dias restantes
        data_hoje = pd.Timestamp(datetime.now())
        df['Dias Restantes'] = (df['Previsão de Entrega'] - data_hoje).dt.days
        
        # Identificar projetos atrasados
        df['Atrasado'] = df['Dias Restantes'] < 0
        
        return df
    except FileNotFoundError:
        st.error("❌ Arquivo 'Roadmap_Projetos_NTD.csv' não encontrado no diretório!")
        st.info("Por favor, certifique-se de que o arquivo está no mesmo diretório do app.py")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = carregar_dados()

if df is not None:
    # ==================== SIDEBAR - FILTROS ====================
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por Portfólio (Multiselect)
    portfolios_disponiveis = sorted(df['Portfólio'].unique())
    portfolios_selecionados = st.sidebar.multiselect(
        "Portfólio",
        options=portfolios_disponiveis,
        default=portfolios_disponiveis
    )
    
    # Filtro por Responsável
    responsaveis_disponiveis = sorted(df['Responsável'].unique())
    responsavel_selecionado = st.sidebar.selectbox(
        "Responsável",
        options=['Todos'] + responsaveis_disponiveis
    )
    
    # Aplicar filtros
    df_filtrado = df[df['Portfólio'].isin(portfolios_selecionados)]
    
    if responsavel_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Responsável'] == responsavel_selecionado]
    
    # ==================== MÉTRICAS NO TOPO ====================
    st.subheader("📈 Indicadores Principais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_projetos = len(df_filtrado)
        st.metric(
            label="Total de Projetos",
            value=total_projetos,
            delta="ativos" if total_projetos > 0 else "nenhum"
        )
    
    with col2:
        # % Médio OKR 2026.1
        if 'Progresso (%)' in df_filtrado.columns:
            media_progresso = df_filtrado['Progresso (%)'].mean()
            st.metric(
                label="% Médio OKR 2026.1",
                value=f"{media_progresso:.1f}%",
                delta=f"{media_progresso - 50:.1f}%" if media_progresso > 50 else None
            )
        else:
            st.metric(
                label="% Médio OKR 2026.1",
                value="N/A",
                delta="Coluna não encontrada"
            )
    
    with col3:
        projetos_atrasados = len(df_filtrado[df_filtrado['Atrasado'] == True])
        delta_color = "inverse" if projetos_atrasados > 0 else "normal"
        st.metric(
            label="Projetos Atrasados",
            value=projetos_atrasados,
            delta=f"{(projetos_atrasados/total_projetos*100):.1f}%" if total_projetos > 0 else "0%",
            delta_color=delta_color
        )
    
    st.markdown("---")
    
    # ==================== VISUALIZAÇÕES ====================
    
    # Abas para organizar visualizações
    tab1, tab2, tab3 = st.tabs(["📊 Progresso dos Projetos", "📅 Timeline Gantt", "🎯 EAP - MXM"])
    
    with tab1:
        st.subheader("Progresso (%) por Projeto")
        
        if len(df_filtrado) > 0:
            # Preparar dados para gráfico de barras
            df_progresso = df_filtrado[['Projeto', 'Progresso (%)']].sort_values('Progresso (%)', ascending=True)
            
            fig_barras = px.bar(
                df_progresso,
                y='Projeto',
                x='Progresso (%)',
                orientation='h',
                color='Progresso (%)',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                title="Progresso de Cada Projeto",
                labels={'Progresso (%)': 'Progresso (%)', 'Projeto': 'Projeto'}
            )
            
            fig_barras.update_layout(
                height=400,
                hovermode='closest',
                xaxis_range=[0, 100]
            )
            
            st.plotly_chart(fig_barras, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum projeto encontrado com os filtros selecionados")
    
    with tab2:
        st.subheader("Timeline de Projetos (Gantt)")
        
        if len(df_filtrado) > 0 and 'Data Início' in df_filtrado.columns:
            # Preparar dados para Gantt
            df_gantt = df_filtrado[['Projeto', 'Data Início', 'Previsão de Entrega', 'Progresso (%)']].copy()
            df_gantt = df_gantt.dropna(subset=['Data Início', 'Previsão de Entrega'])
            
            if len(df_gantt) > 0:
                fig_gantt = px.timeline(
                    df_gantt,
                    x_start='Data Início',
                    x_end='Previsão de Entrega',
                    y='Projeto',
                    color='Progresso (%)',
                    color_continuous_scale='Viridis',
                    title="Timeline de Execução dos Projetos",
                    labels={'Projeto': 'Projeto'}
                )
                
                fig_gantt.update_layout(
                    height=400,
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("⚠️ Dados de data não disponíveis para criar o Gantt")
        elif 'Data Início' not in df_filtrado.columns:
            st.warning("⚠️ Coluna 'Data Início' não encontrada no arquivo CSV")
        else:
            st.warning("⚠️ Nenhum projeto encontrado com os filtros selecionados")
    
    with tab3:
        st.subheader("🎯 Estágio de Implementação Avançada (EAP) - Projeto MXM")
        
        with st.expander("📋 Detalhes da Homologação - Projeto MXM", expanded=False):
            # Dados fictícios de homologação do MXM
            homologacao_data = {
                'Fase': ['Homologação Funcional', 'Homologação Técnica', 'Testes UAT', 'Ajustes v1', 'Ajustes v2', 'Ajustes v3', 'Go-Live Preparação', 'Go-Live'],
                'Responsável': ['Equipe QA', 'Equipe DevOps', 'Cliente', 'Dev Team', 'Dev Team', 'Dev Team', 'Projeto Manager', 'Ops Team'],
                'Status': ['✅ Concluído', '✅ Concluído', '✅ Concluído', '🔄 Em Progresso', '⏳ Aguardando', '⏳ Aguardando', '⏳ Aguardando', '⏳ Aguardando'],
                'Conclusão Prevista': ['01/02/2026', '08/02/2026', '15/02/2026', '22/02/2026', '01/03/2026', '10/03/2026', '20/03/2026', '31/03/2026'],
                'Progresso (%)': [100, 100, 100, 60, 0, 0, 0, 0],
                'Observações': [
                    'Todos os requisitos funcionais validados',
                    'Infraestrutura e performance aprovadas',
                    'Feedback do cliente integrado',
                    'Correções em implementação',
                    'Pendente validação do cliente',
                    'Agendado para próxima semana',
                    'Preparação do ambiente de produção',
                    'Data alvo: 31 de março de 2026'
                ]
            }
            
            df_homologacao = pd.DataFrame(homologacao_data)
            
            # Exibir tabela formatada
            st.dataframe(
                df_homologacao,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Fase': st.column_config.TextColumn('Fase', width='medium'),
                    'Responsável': st.column_config.TextColumn('Responsável', width='medium'),
                    'Status': st.column_config.TextColumn('Status', width='small'),
                    'Conclusão Prevista': st.column_config.TextColumn('Conclusão Prevista', width='small'),
                    'Progresso (%)': st.column_config.ProgressColumn('Progresso', min_value=0, max_value=100),
                    'Observações': st.column_config.TextColumn('Observações', width='large')
                }
            )
            
            # Gráfico de progresso das fases
            st.subheader("📊 Progresso das Fases - MXM")
            fig_eap = px.bar(
                df_homologacao,
                x='Fase',
                y='Progresso (%)',
                color='Progresso (%)',
                color_continuous_scale='Blues',
                range_color=[0, 100],
                title="Progresso das Fases de Homologação",
                labels={'Progresso (%)': 'Progresso (%)', 'Fase': 'Fase'}
            )
            
            fig_eap.update_layout(
                height=350,
                xaxis_tickangle=-45,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_eap, use_container_width=True)
    
    # ==================== RODAPÉ ====================
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; font-size: 12px;'>
            <p>Dashboard atualizado em: {}</p>
            <p>Fonte de dados: Roadmap_Projetos_NTD.csv</p>
        </div>
    """.format(datetime.now().strftime("%d/%m/%Y às %H:%M:%S")), unsafe_allow_html=True)
