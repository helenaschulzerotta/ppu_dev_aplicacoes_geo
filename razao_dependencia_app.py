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
    feature["properties"]["NM_MUN"] = (
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
Este dashboard foi desenvolvido como exercício da disciplina Desenvolvimento de Aplicações Geoespaciais, ofertada pelo Programa de Pós-Graduação em Planejamento Urbano (PPU) da Universidade Federal do Paraná (UFPR) e ministrada pela Prof.ª Dr.ª Silvana Camboim. A aplicação utiliza dados do Censo Demográfico 2022 do IBGE para visualizar a Razão de Dependência dos municípios do Paraná.

A Razão de Dependência é um indicador demográfico que relaciona a população potencialmente dependente (pessoas de 0 a 14 anos e de 65 anos ou mais) com a população em idade potencialmente ativa (15 a 64 anos). O indicador expressa quantas pessoas dependentes existem para cada 100 pessoas em idade ativa, sendo amplamente utilizado para subsidiar análises de planejamento urbano, políticas públicas, demanda por serviços e projeções socioeconômicas.
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

# =====================================================
# Mapa
# =====================================================

st.subheader("Mapa Interativo")

mapa = folium.Map(
    location=[-24.8, -51.5],
    zoom_start=7,
    tiles="CartoDB positron"
)

# Se um município foi selecionado
if municipio != "Todos":

    geojson_filtrado = {
        "type": "FeatureCollection",
        "features": [
            feature
            for feature in geojson_data["features"]
            if feature["properties"]["NM_MUN"] == municipio
        ]
    }

    folium.GeoJson(
        geojson_filtrado,
        tooltip=folium.GeoJsonTooltip(
            fields=["NM_MUN"],
            aliases=["Município:"]
        ),
        style_function=lambda x: {
            "fillColor": "#ff7800",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.8
        }
    ).add_to(mapa)

    # Ajusta o zoom para o município
    st_folium(
        mapa,
        height=600,
        use_container_width=True
    )

else:

    folium.Choropleth(
        geo_data=geojson_data,
        data=tabela,
        columns=["municipio", "razao_dependencia"],
        key_on="feature.properties.NM_MUN",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="Razão de Dependência"
    ).add_to(mapa)

    folium.GeoJson(
        geojson_data,
        tooltip=folium.GeoJsonTooltip(
            fields=["NM_MUN"],
            aliases=["Município:"]
        ),
        style_function=lambda x: {
            "fillColor": "#ff7800",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.8
        }
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
