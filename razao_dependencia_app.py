import streamlit as st
import pandas as pd
import json
import folium

from streamlit_folium import st_folium
import plotly.express as px

# ---------------------------------------------------
# Configuração
# ---------------------------------------------------

st.set_page_config(
    page_title="Razão de Dependência - Paraná",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# Leitura
# ---------------------------------------------------

@st.cache_data
def carregar_dados():

    with open(
    "https://github.com/helenaschulzerotta/ppu_dev_aplicacoes_geo/blob/a45bd7c6d1e7eed4e06abcee65c592446eb1fe81/municipios.geojson",
    encoding="utf-8"
) as f:
    gdf = json.load(f)

    tabela = pd.read_csv(
        "https://github.com/helenaschulzerotta/ppu_dev_aplicacoes_geo/blob/e43d4cb2f415e264e9c8d496ea5db59c1fdc71f9/indicadores_municipios.csv"
    )

    return gdf, tabela

gdf, tabela = carregar_dados()

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------

st.sidebar.title("Filtros")

municipio = st.sidebar.selectbox(
    "Município",
    ["Todos"] + sorted(tabela["municipio"].unique())
)

# ---------------------------------------------------
# Aplicação do filtro
# ---------------------------------------------------

if municipio != "Todos":

    tabela_filtro = tabela[
        tabela["municipio"] == municipio
    ]

    gdf_filtro = gdf[
        gdf["NM_MUN"] == municipio
    ]

else:

    tabela_filtro = tabela.copy()
    gdf_filtro = gdf.copy()

# ---------------------------------------------------
# Título
# ---------------------------------------------------

st.title("Razão de Dependência dos Municípios do Paraná")

st.markdown("""
Dashboard desenvolvido em Streamlit utilizando dados municipais.
""")

# ---------------------------------------------------
# Indicadores
# ---------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Municípios",
    len(tabela_filtro)
)

col2.metric(
    "Razão média",
    round(
        tabela_filtro["razao_dependencia"].mean(),
        2
    )
)

col3.metric(
    "Maior valor",
    round(
        tabela_filtro["razao_dependencia"].max(),
        2
    )
)

# ---------------------------------------------------
# Gráfico
# ---------------------------------------------------

st.subheader("Top 20 Municípios")

top20 = (
    tabela_filtro
    .sort_values(
        "razao_dependencia",
        ascending=False
    )
    .head(20)
)

fig = px.bar(
    top20,
    x="municipio",
    y="razao_dependencia"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ---------------------------------------------------
# Mapa
# ---------------------------------------------------

st.subheader("Mapa Interativo")

centro = [-24.8, -51.5]

m = folium.Map(
    location=centro,
    zoom_start=7
)

folium.Choropleth(
    geo_data=gdf_filtro,
    data=gdf_filtro,
    columns=[
        "NM_MUN",
        "razao_dependencia"
    ],
    key_on="feature.properties.NM_MUN",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.3,
    legend_name="Razão de Dependência"
).add_to(m)

st_folium(
    m,
    width=1200,
    height=600
)

# ---------------------------------------------------
# Tabela
# ---------------------------------------------------

st.subheader("Tabela de Dados")

st.dataframe(
    tabela_filtro,
    use_container_width=True
)
