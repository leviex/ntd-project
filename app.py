import streamlit as st
import pandas as pd

st.title("Dashboard NTD")

st.write("Exemplo simples de dashboard")

data = {
    "Projeto": ["A", "B", "C"],
    "Status": ["Concluído", "Em andamento", "Planejado"],
    "Valor": [10000, 15000, 5000]
}

df = pd.DataFrame(data)

st.dataframe(df)
st.bar_chart(df["Valor"])
