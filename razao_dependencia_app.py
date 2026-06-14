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
    "municipios.geojson",
    encoding="utf-8") 
    as f:
    geojson_data = json.load(f)

    tabela = pd.read_csv(
        "indicadores_municipios.csv"
    )

    return geojson_data, tabela

geojson_data, tabela = carregar_dados()

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------

st.sidebar.title("Filtros")

lista_municipios = sorted(
    tabela["municipio"].dropna().unique()
)

municipio = st.sidebar.selectbox(
    "Município",
    ["Todos"] + list(lista_municipios)
)

if municipio == "Todos":

    tabela_filtro = tabela.copy()

else:

    tabela_filtro = tabela[
        tabela["municipio"] == municipio
    ]

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
    geo_data=geojson_data,
    data=tabela,
    columns=[
        "municipio",
        "razao_dependencia"
    ],
    key_on="feature.properties.NM_MUN",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.3,
    legend_name="Razão de Dependência"
).add_to(m)

folium.GeoJson(
    geojson_data,
    tooltip=folium.GeoJsonTooltip(
        fields=["NM_MUN"],
        aliases=["Município:"]
    )
).add_to(mapa)

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
