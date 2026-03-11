import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Dashboard NTD",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Gestão de Projetos NTD")
st.markdown("---")

@st.cache_data
def carregar_dados():

    df = pd.read_csv("Roadmap_Projetos_NTD.csv")

    # limpar colunas
    df.columns = df.columns.str.strip()

    # renomear para facilitar uso
    df = df.rename(columns={
        "Nome do Projeto": "Projeto",
        "Responsável TI": "Responsavel"
    })

    # converter datas
    df["Previsão de Entrega"] = pd.to_datetime(df["Previsão de Entrega"], errors="coerce")

    # dias restantes
    hoje = pd.Timestamp(datetime.now())
    df["Dias Restantes"] = (df["Previsão de Entrega"] - hoje).dt.days

    # atraso
    df["Atrasado"] = df["Dias Restantes"] < 0

    return df


df = carregar_dados()

# ================= SIDEBAR =================

st.sidebar.header("Filtros")

portfolios = sorted(df["Portfolio"].dropna().unique())

portfolio_sel = st.sidebar.multiselect(
    "Portfolio",
    portfolios,
    default=portfolios
)

responsaveis = sorted(df["Responsavel"].dropna().unique())

responsavel_sel = st.sidebar.selectbox(
    "Responsável",
    ["Todos"] + responsaveis
)

# aplicar filtros

df_filtrado = df[df["Portfolio"].isin(portfolio_sel)]

if responsavel_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Responsavel"] == responsavel_sel]

# ================= MÉTRICAS =================

st.subheader("Indicadores")

col1, col2, col3 = st.columns(3)

total = len(df_filtrado)

col1.metric("Total de Projetos", total)

media_progresso = df_filtrado["Progresso (%)"].mean()

col2.metric(
    "Progresso Médio",
    f"{media_progresso*100:.1f}%"
)

atrasados = len(df_filtrado[df_filtrado["Atrasado"]])

col3.metric("Projetos Atrasados", atrasados)

st.markdown("---")

# ================= GRAFICO PROGRESSO =================

st.subheader("Progresso por Projeto")

df_chart = df_filtrado.sort_values("Progresso (%)")

fig = px.bar(
    df_chart,
    y="Projeto",
    x="Progresso (%)",
    orientation="h",
    color="Progresso (%)",
    color_continuous_scale="RdYlGn",
)

st.plotly_chart(fig, use_container_width=True)

# ================= TABELA =================

st.subheader("Tabela de Projetos")

st.dataframe(df_filtrado, use_container_width=True)

# ================= RODAPÉ =================

st.markdown("---")

st.caption(
    f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
