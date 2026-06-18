"""
app_acessibilidade.py — Dashboard de Acessibilidade Urbana
Requer: streamlit, r5py, geopandas, osmnx, h3pandas, folium,
        streamlit-folium, requests, osmium (apt), Java 21
"""

import os, pathlib, tempfile, subprocess, json, warnings
from datetime import datetime, date, time

import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
import h3pandas          # noqa – registra extensão .h3
import folium
import requests

warnings.filterwarnings("ignore")

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Acessibilidade Urbana",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personalizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Header principal */
.main-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #112240 100%);
    border-left: 4px solid #00b4d8;
    padding: 1.4rem 1.8rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
}
.main-header h1 {
    font-size: 2rem; font-weight: 700;
    color: #e0f7ff; margin: 0; letter-spacing: -0.5px;
}
.main-header .subtitle {
    font-size: 0.85rem; color: #64b5f6; margin-top: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
}

/* Cards de métricas */
.metric-row { display: flex; gap: 12px; margin-bottom: 1.2rem; flex-wrap: wrap; }
.metric-card {
    flex: 1; min-width: 140px;
    background: #112240; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 1rem 1.2rem;
}
.metric-card .label {
    font-size: 0.72rem; color: #64b5f6; text-transform: uppercase;
    letter-spacing: 0.08em; font-weight: 500;
}
.metric-card .value {
    font-size: 1.6rem; font-weight: 700; color: #e0f7ff;
    font-family: 'JetBrains Mono', monospace; line-height: 1.2;
}
.metric-card .delta {
    font-size: 0.75rem; color: #90caf9; margin-top: 0.15rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; border-bottom: 2px solid #1e3a5f;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #90caf9;
    border-radius: 4px 4px 0 0; font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    background: #00b4d8 !important; color: #0d1b2a !important;
    font-weight: 700;
}

/* Sidebar */
section[data-testid="stSidebar"] { background: #0d1b2a; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stDateInput label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stSlider label {
    color: #90caf9 !important; font-size: 0.8rem; font-weight: 500;
}
section[data-testid="stSidebar"] h3 {
    color: #00b4d8; font-size: 0.75rem; text-transform: uppercase;
    letter-spacing: 0.1em; margin-top: 1.2rem; margin-bottom: 0.4rem;
}

/* Botão principal */
.stButton > button {
    background: #00b4d8; color: #0d1b2a; font-weight: 700;
    border: none; border-radius: 6px; padding: 0.6rem 1.4rem;
    width: 100%; transition: background 0.2s;
}
.stButton > button:hover { background: #0096b5; color: #fff; }

/* Tabela de resultados */
.dataframe { font-size: 0.82rem; }

/* Legenda de cores */
.legend-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 0.5rem 0; }
.legend-chip {
    display: flex; align-items: center; gap: 6px;
    font-size: 0.75rem; color: #b0c4de;
}
.legend-chip .dot {
    width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
}

/* Info boxes */
.info-box {
    background: #112240; border-left: 3px solid #00b4d8;
    padding: 0.8rem 1rem; border-radius: 0 6px 6px 0;
    font-size: 0.82rem; color: #90caf9; margin: 0.8rem 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Constantes ───────────────────────────────────────────────────────────────
MUNICIPIOS = {
    "Curitiba, PR":      ("Curitiba, Paraná, Brazil",          "https://download.geofabrik.de/south-america/brazil/sul-latest.osm.pbf"),
    "Anápolis, GO":      ("Anápolis, Goiás, Brazil",           "https://download.geofabrik.de/south-america/brazil/centro-oeste-latest.osm.pbf"),
    "Goiânia, GO":       ("Goiânia, Goiás, Brazil",            "https://download.geofabrik.de/south-america/brazil/centro-oeste-latest.osm.pbf"),
    "São Paulo, SP":     ("São Paulo, São Paulo, Brazil",       "https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf"),
    "Belo Horizonte, MG":("Belo Horizonte, Minas Gerais, Brazil","https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf"),
    "Porto Alegre, RS":  ("Porto Alegre, Rio Grande do Sul, Brazil","https://download.geofabrik.de/south-america/brazil/sul-latest.osm.pbf"),
    "Recife, PE":        ("Recife, Pernambuco, Brazil",        "https://download.geofabrik.de/south-america/brazil/nordeste-latest.osm.pbf"),
    "Fortaleza, CE":     ("Fortaleza, Ceará, Brazil",          "https://download.geofabrik.de/south-america/brazil/nordeste-latest.osm.pbf"),
    "Manaus, AM":        ("Manaus, Amazonas, Brazil",          "https://download.geofabrik.de/south-america/brazil/norte-latest.osm.pbf"),
}

MODOS_LABEL = {
    "Transporte coletivo + Caminhada": "TRANSIT_WALK",
    "Carro":                           "CAR",
    "Bicicleta":                       "BICYCLE",
    "Apenas Caminhada":                "WALK",
}

CATEGORIAS = ["≤ 15 min", "16–30 min", "31–45 min", "46–60 min", "> 60 min", "Sem dados"]
CORES_CAT = {
    "≤ 15 min":  "#1a9641",
    "16–30 min": "#a6d96a",
    "31–45 min": "#ffffbf",
    "46–60 min": "#fdae61",
    "> 60 min":  "#d7191c",
    "Sem dados": "#cccccc",
}

EQUIPAMENTO_TAGS = {
    "Saúde":              {"amenity": ["hospital", "clinic", "health_post"]},
    "Educação":           {"amenity": ["school", "kindergarten"]},
    "Assistência Social": {"amenity": "social_facility"},
}

LIMIAR_CRITICO = 45  # minutos

# ─── Session state ────────────────────────────────────────────────────────────
for k in ("network_ready", "resultados_A", "resultados_B", "hex_grid",
          "muni_poly", "equipamentos", "config"):
    if k not in st.session_state:
        st.session_state[k] = None

# ─── Sidebar — configuração ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.8rem 0 0.4rem;'>
        <span style='font-size:2rem'>🗺️</span><br>
        <span style='color:#00b4d8; font-weight:700; font-size:1rem'>Acessibilidade Urbana</span><br>
        <span style='color:#64b5f6; font-size:0.72rem'>r5py · OSM · GTFS · H3</span>
    </div>
    <hr style='border-color:#1e3a5f; margin: 0.8rem 0'>
    """, unsafe_allow_html=True)

    st.markdown("### 📍 Município")
    municipio_sel = st.selectbox(
        "Município",
        options=list(MUNICIPIOS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    osm_query, pbf_url = MUNICIPIOS[municipio_sel]

    st.markdown("### 🚌 Arquivo GTFS")
    gtfs_path = st.text_input(
        "Caminho para o .zip",
        placeholder="/caminho/para/gtfs.zip",
        help="Arquivo GTFS do município selecionado. No Colab, monte o Drive e informe o caminho completo.",
    )

    st.markdown("### 📅 Partida")
    col_d, col_h = st.columns([3, 2])
    with col_d:
        data_partida = st.date_input("Data", value=date(2026, 6, 2))
    with col_h:
        hora_partida = st.time_input("Hora", value=time(8, 0))

    st.markdown("### 🚗 Modos de transporte")
    modo_a = st.selectbox("Modo A (principal)", options=list(MODOS_LABEL.keys()), index=0)
    modo_b = st.selectbox("Modo B (comparação)", options=list(MODOS_LABEL.keys()), index=1)

    st.markdown("### ⚙️ Parâmetros")
    tempo_max = st.slider("Tempo máximo (min)", min_value=15, max_value=120, value=60, step=5)
    h3_res    = st.select_slider("Resolução H3", options=[7, 8, 9], value=8,
                                  help="7 ≈ 5,2 km² · 8 ≈ 0,7 km² · 9 ≈ 0,1 km²")

    st.markdown("<br>", unsafe_allow_html=True)
    rodar = st.button("▶  Executar análise")

    st.markdown("""
    <hr style='border-color:#1e3a5f'>
    <div style='font-size:0.7rem; color:#445566; text-align:center; padding-bottom:0.5rem'>
    Dados: OpenStreetMap · Geofabrik<br>Motor: R5 via r5py
    </div>
    """, unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>Acessibilidade Urbana — {municipio_sel}</h1>
    <div class="subtitle">
        {modo_a} &nbsp;·&nbsp; {modo_b} &nbsp;·&nbsp;
        Partida {data_partida.strftime("%d/%m/%Y")} às {hora_partida.strftime("%H:%M")} &nbsp;·&nbsp;
        H3 res {h3_res} &nbsp;·&nbsp; máx {tempo_max} min
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Funções de análise ───────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def construir_rede(pbf_url: str, osm_query: str, gtfs_zip: str):
    """Baixa PBF, recorta para o município e constrói TransportNetwork."""
    import r5py

    tmp = pathlib.Path(tempfile.mkdtemp())
    regional_pbf = tmp / "regional.osm.pbf"
    clip_pbf     = tmp / "municipio.osm.pbf"
    poly_file    = tmp / "boundary.geojson"

    # download PBF
    r = requests.get(pbf_url, stream=True)
    with open(regional_pbf, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)

    # polígono municipal
    muni = ox.geocode_to_gdf(osm_query)
    poly = muni.to_crs("EPSG:4326").geometry.iloc[0]
    poly_file.write_text(json.dumps({
        "type": "Feature", "geometry": poly.__geo_interface__, "properties": {}
    }))

    # recorte
    subprocess.run(["osmium", "extract", "--polygon", str(poly_file),
                    "--output", str(clip_pbf), "--overwrite", str(regional_pbf)],
                   check=True, capture_output=True)

    network = r5py.TransportNetwork(str(clip_pbf), [gtfs_zip])
    return network, muni


@st.cache_data(show_spinner=False)
def gerar_grid(osm_query: str, h3_res: int):
    muni = ox.geocode_to_gdf(osm_query)
    grid = muni.h3.polyfill_resample(h3_res).reset_index()
    grid = grid.rename(columns={[c for c in grid.columns if "h3" in c][0]: "id"})
    grid = grid.to_crs("EPSG:4326")
    origens = grid.copy().to_crs("EPSG:31982")
    origens["geometry"] = origens.geometry.centroid
    origens = origens.to_crs("EPSG:4326")
    return grid, origens, muni


@st.cache_data(show_spinner=False)
def buscar_equipamentos(osm_query: str):
    equipamentos = {}
    for nome, tags in EQUIPAMENTO_TAGS.items():
        gdf = ox.features_from_place(osm_query, tags=tags)
        gdf = gdf.reset_index().rename(columns={"osmid": "id"})
        gdf = gdf.to_crs("EPSG:31982")
        gdf["geometry"] = gdf.geometry.centroid
        gdf = gdf.to_crs("EPSG:4326")
        gdf["nome"] = gdf.get("name", pd.Series(dtype=str)).fillna(nome)
        gdf["tipo"] = nome
        gdf = gdf[["id", "nome", "tipo", "geometry"]].copy()
        gdf["id"] = gdf["id"].astype(str)
        equipamentos[nome] = gdf
    return equipamentos


def calcular_acessibilidade(_network, origens, destinos, modo_str,
                             partida: datetime, max_min: int, hex_grid):
    import r5py

    MODOS_R5 = {
        "TRANSIT_WALK": [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
        "CAR":          [r5py.TransportMode.CAR],
        "BICYCLE":      [r5py.TransportMode.BICYCLE],
        "WALK":         [r5py.TransportMode.WALK],
    }
    modos = MODOS_R5[modo_str]

    ttm = r5py.TravelTimeMatrix(
        _network,
        origins=origens,
        destinations=destinos,
        transport_modes=modos,
        departure=partida,
        max_time=pd.Timedelta(minutes=max_min),
    )
    melhor = (
        ttm.groupby("from_id")["travel_time"]
        .min()
        .dt.total_seconds()
        .div(60)
        .reset_index()
        .rename(columns={"from_id": "id", "travel_time": "tempo_min"})
    )
    resultado = hex_grid.merge(melhor, on="id", how="left")
    bins   = [0, 15, 30, 45, 60, float("inf")]
    labels = ["≤ 15 min", "16–30 min", "31–45 min", "46–60 min", "> 60 min"]
    resultado["categoria"] = pd.cut(resultado["tempo_min"], bins=bins, labels=labels)
    resultado["categoria"] = resultado["categoria"].cat.add_categories("Sem dados")
    resultado["categoria"] = resultado["categoria"].fillna("Sem dados")
    return resultado


def construir_mapa(hex_grid, resultados_A, resultados_B, equipamentos,
                   centro, label_a, label_b):
    m = folium.Map(location=centro, zoom_start=11, tiles="CartoDB positron")

    for equip_nome in EQUIPAMENTO_TAGS:
        for (label, res) in [(label_a, resultados_A), (label_b, resultados_B)]:
            df = hex_grid.merge(
                res[equip_nome][["id", "tempo_min", "categoria"]], on="id", how="left"
            ).to_crs("EPSG:4326")
            fg = folium.FeatureGroup(name=f"{equip_nome} — {label}", show=(label == label_a))
            for _, row in df.iterrows():
                cat = str(row.get("categoria", "Sem dados"))
                cor = CORES_CAT.get(cat, "#cccccc")
                t   = row.get("tempo_min")
                tip = (f"<b>{equip_nome}</b><br>Modo: {label}<br>"
                       f"Tempo: {t:.0f} min<br>Faixa: {cat}"
                       if pd.notna(t) else f"<b>{equip_nome}</b><br>Sem acesso")
                folium.GeoJson(
                    row.geometry.__geo_interface__,
                    style_function=lambda f, c=cor: {
                        "fillColor": c, "color": "#aaa", "weight": 0.3, "fillOpacity": 0.7,
                    },
                    tooltip=tip,
                ).add_to(fg)
            fg.add_to(m)

        # pontos dos equipamentos
        gdf_eq = equipamentos[equip_nome]
        fg_eq  = folium.FeatureGroup(name=f"📍 {equip_nome} (equipamentos)", show=False)
        for _, row in gdf_eq.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=4, color="#fff", fill=True, fill_color="#00b4d8",
                fill_opacity=0.9, weight=1,
                tooltip=row.get("nome", equip_nome),
            ).add_to(fg_eq)
        fg_eq.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def resumo_estatistico(resultados, label):
    rows = []
    for equip_nome, df in resultados.items():
        val = df["tempo_min"].dropna()
        rows.append({
            "Equipamento":  equip_nome,
            "Modo":         label,
            "Mediana (min)": round(val.median(), 1) if len(val) else None,
            "Média (min)":   round(val.mean(), 1)   if len(val) else None,
            "% ≤ 30 min":    round((val <= 30).mean() * 100, 1) if len(val) else None,
            "% > 60 min":    round((val > 60).mean() * 100, 1)  if len(val) else None,
            "Sem dados":     int(df["tempo_min"].isna().sum()),
        })
    return pd.DataFrame(rows)


# ─── Execução principal ───────────────────────────────────────────────────────
if rodar:
    if not gtfs_path or not pathlib.Path(gtfs_path).exists():
        st.error("❌ Arquivo GTFS não encontrado. Verifique o caminho informado na barra lateral.")
        st.stop()

    partida = datetime.combine(data_partida, hora_partida)
    modo_a_str = MODOS_LABEL[modo_a]
    modo_b_str = MODOS_LABEL[modo_b]

    with st.status("Preparando análise...", expanded=True) as status:
        st.write("⬇️ Baixando rede OSM e construindo TransportNetwork…")
        network, muni_poly = construir_rede(pbf_url, osm_query, gtfs_path)

        st.write("📐 Gerando grade hexagonal H3…")
        hex_grid, origens, muni_poly = gerar_grid(osm_query, h3_res)

        st.write("🔍 Coletando equipamentos públicos…")
        equipamentos = buscar_equipamentos(osm_query)

        st.write(f"🚦 Calculando acessibilidade — {modo_a}…")
        resultados_A = {}
        for nome, dest in equipamentos.items():
            resultados_A[nome] = calcular_acessibilidade(
                network, origens, dest, modo_a_str, partida, tempo_max, hex_grid
            )

        st.write(f"🚦 Calculando acessibilidade — {modo_b}…")
        resultados_B = {}
        for nome, dest in equipamentos.items():
            resultados_B[nome] = calcular_acessibilidade(
                network, origens, dest, modo_b_str, partida, tempo_max, hex_grid
            )

        st.session_state["network_ready"] = True
        st.session_state["resultados_A"]  = resultados_A
        st.session_state["resultados_B"]  = resultados_B
        st.session_state["hex_grid"]      = hex_grid
        st.session_state["muni_poly"]     = muni_poly
        st.session_state["equipamentos"]  = equipamentos
        st.session_state["config"] = {
            "municipio": municipio_sel, "modo_a": modo_a, "modo_b": modo_b,
            "partida": partida, "tempo_max": tempo_max, "h3_res": h3_res,
            "osm_query": osm_query,
        }
        status.update(label="✅ Análise concluída!", state="complete", expanded=False)


# ─── Resultados ───────────────────────────────────────────────────────────────
if st.session_state["network_ready"]:
    resultados_A = st.session_state["resultados_A"]
    resultados_B = st.session_state["resultados_B"]
    hex_grid      = st.session_state["hex_grid"]
    muni_poly     = st.session_state["muni_poly"]
    equipamentos  = st.session_state["equipamentos"]
    cfg           = st.session_state["config"]

    label_a = cfg["modo_a"]
    label_b = cfg["modo_b"]

    # ── Métricas de topo ────────────────────────────────────────────────────
    hex_total = len(hex_grid)

    # melhor equipamento: saúde, modo A
    med_saude_A = resultados_A["Saúde"]["tempo_min"].median()
    med_saude_B = resultados_B["Saúde"]["tempo_min"].median()
    pct_30_A    = (resultados_A["Saúde"]["tempo_min"].dropna() <= 30).mean() * 100
    sem_acesso  = resultados_A["Saúde"]["tempo_min"].isna().sum()

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Hexágonos analisados</div>
            <div class="value">{hex_total:,}</div>
            <div class="delta">H3 resolução {cfg['h3_res']}</div>
        </div>
        <div class="metric-card">
            <div class="label">Mediana — Saúde ({label_a})</div>
            <div class="value">{med_saude_A:.0f} min</div>
            <div class="delta">vs {med_saude_B:.0f} min ({label_b})</div>
        </div>
        <div class="metric-card">
            <div class="label">Cobertura ≤ 30 min — Saúde</div>
            <div class="value">{pct_30_A:.0f}%</div>
            <div class="delta">hexágonos por {label_a}</div>
        </div>
        <div class="metric-card">
            <div class="label">Sem acesso — Saúde</div>
            <div class="value">{sem_acesso:,}</div>
            <div class="delta">além do limite de {cfg['tempo_max']} min</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ────────────────────────────────────────────────────────────────
    tab_mapa, tab_stats, tab_equidade, tab_dados = st.tabs([
        "🗺️  Mapa interativo",
        "📊  Estatísticas",
        "⚖️  Equidade",
        "📋  Dados brutos",
    ])

    # ── TAB 1 — Mapa ────────────────────────────────────────────────────────
    with tab_mapa:
        st.markdown("""
        <div class="info-box">
        Use o controle de camadas (canto superior direito do mapa) para alternar entre
        equipamentos e modos. Clique sobre um hexágono para ver o tempo de viagem.
        </div>
        """, unsafe_allow_html=True)

        # Legenda
        legenda_html = '<div class="legend-row">' + "".join(
            f'<div class="legend-chip"><div class="dot" style="background:{CORES_CAT[c]}"></div>{c}</div>'
            for c in CATEGORIAS
        ) + "</div>"
        st.markdown(legenda_html, unsafe_allow_html=True)

        try:
            from streamlit_folium import st_folium
            centro = [muni_poly.geometry.centroid.y.iloc[0],
                      muni_poly.geometry.centroid.x.iloc[0]]
            m = construir_mapa(hex_grid, resultados_A, resultados_B,
                               equipamentos, centro, label_a, label_b)
            st_folium(m, width="100%", height=580, returned_objects=[])
        except ImportError:
            st.warning("Instale `streamlit-folium` para exibir o mapa interativo: `pip install streamlit-folium`")
            st.info("O mapa também pode ser exportado como HTML na aba Dados Brutos.")

    # ── TAB 2 — Estatísticas ────────────────────────────────────────────────
    with tab_stats:
        df_A = resumo_estatistico(resultados_A, label_a)
        df_B = resumo_estatistico(resultados_B, label_b)
        df_resumo = pd.concat([df_A, df_B], ignore_index=True)

        st.markdown("#### Resumo por equipamento e modo")
        st.dataframe(
            df_resumo.set_index(["Equipamento", "Modo"]),
            use_container_width=True,
        )

        st.markdown("#### Distribuição por faixa de tempo")
        equip_sel = st.selectbox("Equipamento", options=list(EQUIPAMENTO_TAGS.keys()))

        col1, col2 = st.columns(2)
        for col, (label, res) in zip([col1, col2], [(label_a, resultados_A), (label_b, resultados_B)]):
            with col:
                st.markdown(f"**{label}**")
                dist = res[equip_sel]["categoria"].value_counts()
                dist = dist.reindex(CATEGORIAS, fill_value=0)
                st.bar_chart(dist.rename("Hexágonos"))

    # ── TAB 3 — Equidade ────────────────────────────────────────────────────
    with tab_equidade:
        st.markdown(f"""
        <div class="info-box">
        Zonas <b>críticas</b>: hexágonos com tempo &gt; {LIMIAR_CRITICO} min por {label_a}.
        Representam territórios com menor acessibilidade pelo transporte coletivo.
        </div>
        """, unsafe_allow_html=True)

        criticos_rows = []
        for equip_nome, df in resultados_A.items():
            n_crit = int((df["tempo_min"] > LIMIAR_CRITICO).sum())
            n_tot  = len(df)
            delta  = resultados_A[equip_nome]["tempo_min"] - resultados_B[equip_nome]["tempo_min"]
            pior_a = int((delta > 0).sum())
            criticos_rows.append({
                "Equipamento":             equip_nome,
                "Hexágonos críticos":      n_crit,
                "% críticos":              round(n_crit / n_tot * 100, 1),
                f"A mais lento que B (nº)": pior_a,
                f"A mais lento que B (%)":  round(pior_a / n_tot * 100, 1),
            })

        st.dataframe(pd.DataFrame(criticos_rows).set_index("Equipamento"),
                     use_container_width=True)

        st.markdown("#### Diferença de tempo A − B por equipamento")
        equip_eq = st.selectbox("Equipamento ", options=list(EQUIPAMENTO_TAGS.keys()),
                                key="equip_eq")
        delta_df = (
            resultados_A[equip_eq]["tempo_min"]
            .sub(resultados_B[equip_eq]["tempo_min"])
            .dropna()
        )
        bins_delta = [-60, -30, -15, 0, 15, 30, 60]
        labels_d   = ["A muito melhor", "A melhor", "A ligeiramente melhor",
                      "B ligeiramente melhor", "B melhor", "B muito melhor"]
        delta_cat  = pd.cut(delta_df, bins=bins_delta, labels=labels_d)
        st.bar_chart(delta_cat.value_counts().sort_index().rename("Hexágonos"))

    # ── TAB 4 — Dados brutos ────────────────────────────────────────────────
    with tab_dados:
        st.markdown("#### Exportar resultados")
        equip_dl = st.selectbox("Equipamento  ", options=list(EQUIPAMENTO_TAGS.keys()),
                                key="equip_dl")
        modo_dl  = st.radio("Modo", [label_a, label_b], horizontal=True)
        df_dl    = resultados_A[equip_dl] if modo_dl == label_a else resultados_B[equip_dl]

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv = df_dl[["id", "tempo_min", "categoria"]].to_csv(index=False)
            st.download_button(
                "⬇️ Baixar CSV",
                data=csv,
                file_name=f"acessibilidade_{equip_dl.lower().replace(' ', '_')}_{modo_dl[:3]}.csv",
                mime="text/csv",
            )
        with col_dl2:
            geojson = df_dl[["id", "tempo_min", "categoria", "geometry"]].to_json()
            st.download_button(
                "⬇️ Baixar GeoJSON",
                data=geojson,
                file_name=f"acessibilidade_{equip_dl.lower().replace(' ', '_')}_{modo_dl[:3]}.geojson",
                mime="application/json",
            )

        st.markdown("#### Amostra dos dados")
        st.dataframe(
            df_dl[["id", "tempo_min", "categoria"]].dropna().head(50),
            use_container_width=True,
        )

else:
    # ── Estado inicial: instrução de uso ────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding: 4rem 2rem; color: #445566;'>
        <div style='font-size: 3rem; margin-bottom: 1rem'>⚙️</div>
        <div style='font-size: 1.1rem; color: #64b5f6; font-weight: 600; margin-bottom: 0.5rem'>
            Configure a análise na barra lateral
        </div>
        <div style='font-size: 0.85rem; color: #445566; max-width: 420px; margin: 0 auto'>
            Selecione o município, informe o arquivo GTFS, ajuste a data/hora e os modos
            de transporte — depois clique em <b>Executar análise</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)
