import streamlit as st
import pandas as pd
import json
import folium

from streamlit_folium import st_folium
import plotly.express as px

from unidecode import unidecode

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

    with open("municipios.geojson", encoding="utf-8") as f:
        geojson_data = json.load(f)

    tabela = pd.read_csv(
        "indicadores_municipios.csv"
    )

    return geojson_data, tabela

geojson_data, tabela = carregar_dados()

# ---------------------------------------------------
# Padronização entre arquivos
# ---------------------------------------------------

tabela["municipio"] = (
    tabela["municipio"]
    .astype(str)
    .str.upper()
    .str.strip()
)

tabela["razao_dependencia"] = pd.to_numeric(
    tabela["razao_dependencia"],
    errors="coerce"
)

tabela["municipio"] = (
    tabela["municipio"]
    .astype(str)
    .apply(unidecode)
    .str.upper()
    .str.strip()
)

for feature in geojson_data["features"]:
    feature["properties"]["NM_MUN_PAD"] = (
        unidecode(
            feature["properties"]["NM_MUN"]
        )
        .upper()
        .strip()
    )

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

st.subheader("Razão de Dependência")

mun = (
    tabela_filtro
    .sort_values(
        "razao_dependencia",
        ascending=False
    )
    .head(20)
)

fig = px.bar(
    mun,
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

st.write("Municípios CSV:", len(tabela)) #report

nomes_geojson = [
    f["properties"]["NM_MUN_PAD"]
    for f in geojson_data["features"]
] #report

st.write(
    "Correspondências:",
    tabela["municipio_pad"].isin(nomes_geojson).sum()
) #report

st.subheader("Mapa")

mapa = folium.Map(
    location=[-24.8, -51.5],
    zoom_start=7
)

folium.Choropleth(
    geo_data=geojson_data,
    data=tabela,
    columns=["municipio_pad", "razao_dependencia"],
    key_on="feature.properties.NM_MUN_PAD",
    fill_color="YlGnBu",
    nan_fill_color="white",
    legend_name="Razão de Dependência"
).add_to(mapa)

st_folium(
    mapa,
    height=600,
    use_container_width=True
)

# ---------------------------------------------------
# Tabela
# ---------------------------------------------------

st.subheader("Tabela de Dados")

st.dataframe(
    tabela_filtro,
    use_container_width=True
)
