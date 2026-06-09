"""
app.py  — v3  (GeoJsonLayer + Tabs + st.metric)
================================================
Mejoras respecto a v2:
  · GeoJsonLayer como fondo (relleno gris suave, bordes delimitadores).
  · map_style="light" (mapa base claro de Carto/OpenStreetMap, sin token Mapbox).
  · Layout con st.tabs: Mapa | Tabla Comparativa | Rendimiento.
  · st.metric para destacar Distancia, Tiempo y Pasos del ganador.
  · st.multiselect para selección compacta de algoritmos en sidebar.
  · Paleta de colores mejorada: ruta en rojo coral, origen/destino en ámbar.
  · ScatterplotLayer y LineLayer por encima del GeoJsonLayer.
"""

import json
import time
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from data import (
    LISTA_PROVINCIAS,
    get_adyacentes,
    get_coords,
    get_departamento,
    get_departamentos,
    get_grafo,
    get_provincias_por_departamento,
)

from tsp import (
    vecino_mas_cercano,
    fuerza_bruta_tsp,
    dfs_poda_tsp,
    bfs_poda_tsp,
    astar_tsp,
    two_opt_tsp,
    algoritmo_genetico_tsp,
)

from tsp.tsp_utils import (
    crear_resultado_tsp,
    validar_provincias_tsp,
)
# ---------------------------------------------------------------------------
# Importaciones de algoritmos (con stubs defensivos)
# ---------------------------------------------------------------------------
try:
    from algorithms import (
        astar,
        bellman_ford,
        bidireccional,
        dijkstra,
        floyd_warshall,
        greedy_bfs,
        ucs,
    )
except ImportError:
    def _stub(grafo, origen, destino, coords=None):
        return None, None

    dijkstra = astar = bellman_ford = bidireccional = greedy_bfs = ucs = _stub

    def floyd_warshall(grafo, origen=None, destino=None, coords=None):
        return None, None


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES Y HELPERS
# ═══════════════════════════════════════════════════════════════════════════

GEOJSON_PATH = Path(__file__).parent / "peru_provincial_simple.geojson"

ALGORITMOS_DISPONIBLES: dict[str, callable] = {
    "Dijkstra":       dijkstra,
    "A*":             astar,
    "Bellman-Ford":   bellman_ford,
    "Bidireccional":  bidireccional,
    "Greedy BFS":     greedy_bfs,
    "Floyd-Warshall": floyd_warshall,
    "UCS":            ucs,
}

ALGORITMOS_TSP_DISPONIBLES: dict[str, callable] = {
    "Vecino más cercano": vecino_mas_cercano,
    "Fuerza bruta": fuerza_bruta_tsp,
    "DFS con poda": dfs_poda_tsp,
    "BFS con poda": bfs_poda_tsp,
    "A* para TSP": astar_tsp,
    "2-opt": two_opt_tsp,
    "Algoritmo genético": algoritmo_genetico_tsp,
}
# Paleta de colores (RGBA)
COLOR_NODO_BASE    = [160, 170, 180, 140]   # gris azulado tenue
COLOR_NODO_CAMINO  = [59,  130, 246, 230]   # azul vivo (nodos intermedios)
COLOR_ORIGEN       = [245, 158,  11, 255]   # ámbar (origen)
COLOR_DESTINO      = [16,  185, 129, 255]   # verde esmeralda (destino)
COLOR_LINEA        = [239,  68,  68, 220]   # rojo coral (ruta)
COLOR_TEXTO        = [30,   30,  30, 255]   # casi negro

COLORES_ALGORITMOS = {
    # Ruta corta
    "Dijkstra": [239, 68, 68, 230],
    "A*": [59, 130, 246, 230],
    "Bellman-Ford": [16, 185, 129, 230],
    "Bidireccional": [245, 158, 11, 230],
    "Greedy BFS": [168, 85, 247, 230],
    "Floyd-Warshall": [236, 72, 153, 230],
    "UCS": [20, 184, 166, 230],

    # TSP
    "Vecino más cercano": [239, 68, 68, 230],
    "Fuerza bruta": [59, 130, 246, 230],
    "DFS con poda": [16, 185, 129, 230],
    "BFS con poda": [245, 158, 11, 230],
    "A* para TSP": [168, 85, 247, 230],
    "2-opt": [236, 72, 153, 230],
    "Algoritmo genético": [20, 184, 166, 230],
}

# Vista inicial centrada en Perú
VISTA_PERU = pdk.ViewState(
    latitude=-9.5,
    longitude=-75.0,
    zoom=4.6,
    pitch=0,
    bearing=0,
)


def _indice_defecto(lista: list[str], candidatos: list[str], fallback: int = 0) -> int:
    """Índice del primer candidato hallado (case-insensitive), o fallback."""
    lista_up = [p.upper() for p in lista]
    for c in candidatos:
        try:
            return lista_up.index(c.upper())
        except ValueError:
            continue
    return fallback


# ═══════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS (cacheada)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _cargar_datos() -> tuple[dict, dict, list[dict]]:
    """Grafo, coords y lista de nodos para Pydeck. Se ejecuta UNA sola vez."""
    grafo  = get_grafo()
    coords = {p: get_coords(p) for p in grafo}
    nodos  = [
        {"name": p, "lat": coords[p][0], "lon": coords[p][1]}
        for p in grafo
        if coords[p][0] is not None
    ]
    return grafo, coords, nodos


@st.cache_data(show_spinner=False)
def _cargar_geojson() -> dict | None:
    """Lee el GeoJSON provincial para el GeoJsonLayer. Devuelve None si no existe."""
    if not GEOJSON_PATH.exists():
        return None
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL MAPA PYDECK
# ═══════════════════════════════════════════════════════════════════════════

def _construir_mapa(
    coords:        dict,
    nodos_df:      list[dict],
    geojson_data:  dict | None,
    camino:        list[str] | None = None,
) -> pdk.Deck:
    """
    Capas (de abajo hacia arriba):
      0. GeoJsonLayer   — polígonos provinciales (fondo gris suave)
      1. ScatterplotLayer — todos los nodos (gris tenue)
      2. LineLayer        — segmentos de la ruta (rojo coral)  ← solo si hay camino
      3. ScatterplotLayer — nodos del camino (azul/ámbar/verde) ← solo si hay camino
      4. TextLayer        — etiquetas de nodos del camino       ← solo si hay camino
    """
    capas: list[pdk.Layer] = []

    # ── Capa 0: GeoJsonLayer ────────────────────────────────────────────────
    if geojson_data is not None:
        capa_geojson = pdk.Layer(
            "GeoJsonLayer",
            data=geojson_data,
            stroked=True,
            filled=True,
            get_fill_color=[240, 242, 245, 200],   # gris/blanco muy suave, semitransparente
            get_line_color=[180, 188, 200, 220],    # gris medio para los bordes
            line_width_min_pixels=1,
            pickable=False,
        )
        capas.append(capa_geojson)

    # ── Capa 1: todos los nodos ─────────────────────────────────────────────
    capa_nodos = pdk.Layer(
        "ScatterplotLayer",
        data=nodos_df,
        get_position=["lon", "lat"],
        get_radius=6_500,
        get_fill_color=COLOR_NODO_BASE,
        pickable=True,
        auto_highlight=True,
    )
    capas.append(capa_nodos)

    # ── Capas del camino (solo si existe) ───────────────────────────────────
    if camino and len(camino) >= 2:

        # Datos de nodos del camino con colores diferenciados
        nodos_camino = []
        for i, p in enumerate(camino):
            lat, lon = coords.get(p, (None, None))
            if lat is None:
                continue
            if i == 0:
                color = COLOR_ORIGEN
            elif i == len(camino) - 1:
                color = COLOR_DESTINO
            else:
                color = COLOR_NODO_CAMINO
            nodos_camino.append({"name": p, "lat": lat, "lon": lon, "color": color})

        # Datos de aristas del camino
        aristas = []
        for i in range(len(camino) - 1):
            a, b = camino[i], camino[i + 1]
            lat_a, lon_a = coords.get(a, (None, None))
            lat_b, lon_b = coords.get(b, (None, None))
            if None in (lat_a, lon_a, lat_b, lon_b):
                continue
            aristas.append({
                "src_lon": lon_a, "src_lat": lat_a,
                "tgt_lon": lon_b, "tgt_lat": lat_b,
            })

        # Capa 2: líneas de la ruta
        capa_lineas = pdk.Layer(
            "LineLayer",
            data=aristas,
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["tgt_lon", "tgt_lat"],
            get_color=COLOR_LINEA,
            get_width=5,
            pickable=False,
            width_min_pixels=2,
        )

        # Capa 3: nodos del camino (encima de la ruta)
        capa_nodos_camino = pdk.Layer(
            "ScatterplotLayer",
            data=nodos_camino,
            get_position=["lon", "lat"],
            get_radius=14_000,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
            stroked=True,
            get_line_color=[255, 255, 255, 200],
            line_width_min_pixels=2,
        )

        # Capa 4: etiquetas
        capa_texto = pdk.Layer(
            "TextLayer",
            data=nodos_camino,
            get_position=["lon", "lat"],
            get_text="name",
            get_size=12,
            get_color=COLOR_TEXTO,
            get_alignment_baseline="'bottom'",
            get_pixel_offset=[0, -20],
            pickable=False,
            billboard=True,
        )

        capas += [capa_lineas, capa_nodos_camino, capa_texto]

    return pdk.Deck(
        layers=capas,
        initial_view_state=VISTA_PERU,
        tooltip={"text": "{name}"},
        map_style="light",           # Carto Light, sin token Mapbox
    )

def _construir_mapa_multiple(
    coords: dict,
    nodos_df: list[dict],
    geojson_data: dict | None,
    caminos_por_algoritmo: dict[str, list[str]] | None = None,
) -> pdk.Deck:
    """
    Construye un mapa mostrando varias rutas al mismo tiempo.

    Si varias rutas pasan por el mismo tramo, se aplica un pequeño
    desplazamiento visual para que no queden totalmente superpuestas.
    """

    capas: list[pdk.Layer] = []

    # Capa 0: GeoJSON provincial
    if geojson_data is not None:
        capa_geojson = pdk.Layer(
            "GeoJsonLayer",
            data=geojson_data,
            stroked=True,
            filled=True,
            get_fill_color=[240, 242, 245, 200],
            get_line_color=[180, 188, 200, 220],
            line_width_min_pixels=1,
            pickable=False,
        )
        capas.append(capa_geojson)

    # Capa 1: todos los nodos
    capa_nodos = pdk.Layer(
        "ScatterplotLayer",
        data=nodos_df,
        get_position=["lon", "lat"],
        get_radius=6_500,
        get_fill_color=COLOR_NODO_BASE,
        pickable=True,
        auto_highlight=True,
    )
    capas.append(capa_nodos)

    if not caminos_por_algoritmo:
        return pdk.Deck(
            layers=capas,
            initial_view_state=VISTA_PERU,
            tooltip={"text": "{name}"},
            map_style="light",
        )

    caminos_validos = {
        algoritmo: camino
        for algoritmo, camino in caminos_por_algoritmo.items()
        if camino and len(camino) >= 2
    }

    if not caminos_validos:
        return pdk.Deck(
            layers=capas,
            initial_view_state=VISTA_PERU,
            tooltip={"text": "{name}"},
            map_style="light",
        )

    todas_las_lineas = []
    nodos_destacados = {}

    algoritmos = list(caminos_validos.keys())
    cantidad_algoritmos = len(algoritmos)

    # Separación visual entre líneas.
    # No afecta los cálculos, solo la visualización.
    separacion_visual = 0.025

    for indice_algoritmo, algoritmo in enumerate(algoritmos):
        camino = caminos_validos[algoritmo]

        color = COLORES_ALGORITMOS.get(
            algoritmo,
            [100, 100, 100, 220],
        )

        desplazamiento_base = (
            indice_algoritmo - (cantidad_algoritmos - 1) / 2
        ) * separacion_visual

        # Líneas de la ruta
        for i in range(len(camino) - 1):
            a = camino[i]
            b = camino[i + 1]

            lat_a, lon_a = coords.get(a, (None, None))
            lat_b, lon_b = coords.get(b, (None, None))

            if None in (lat_a, lon_a, lat_b, lon_b):
                continue

            dx = lon_b - lon_a
            dy = lat_b - lat_a
            longitud = (dx ** 2 + dy ** 2) ** 0.5

            if longitud == 0:
                offset_lon = 0
                offset_lat = 0
            else:
                # Vector perpendicular al segmento.
                offset_lon = (-dy / longitud) * desplazamiento_base
                offset_lat = (dx / longitud) * desplazamiento_base

            todas_las_lineas.append({
                "src_lon": lon_a + offset_lon,
                "src_lat": lat_a + offset_lat,
                "tgt_lon": lon_b + offset_lon,
                "tgt_lat": lat_b + offset_lat,
                "algoritmo": algoritmo,
                "color": color,
            })

        # Nodos destacados, sin desplazar
        for posicion, provincia in enumerate(camino):
            lat, lon = coords.get(provincia, (None, None))

            if lat is None:
                continue

            if provincia not in nodos_destacados:
                nodos_destacados[provincia] = {
                    "name": provincia,
                    "lat": lat,
                    "lon": lon,
                    "color": COLOR_NODO_CAMINO,
                }

            if posicion == 0:
                nodos_destacados[provincia]["color"] = COLOR_ORIGEN

            if posicion == len(camino) - 1:
                nodos_destacados[provincia]["color"] = COLOR_DESTINO

    # Capa 2: líneas de todos los algoritmos
    if todas_las_lineas:
        capa_lineas = pdk.Layer(
            "LineLayer",
            data=todas_las_lineas,
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["tgt_lon", "tgt_lat"],
            get_color="color",
            get_width=6,
            pickable=True,
            width_min_pixels=3,
        )
        capas.append(capa_lineas)

    # Capa 3: nodos destacados
    nodos_camino = list(nodos_destacados.values())

    if nodos_camino:
        capa_nodos_camino = pdk.Layer(
            "ScatterplotLayer",
            data=nodos_camino,
            get_position=["lon", "lat"],
            get_radius=14_000,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
            stroked=True,
            get_line_color=[255, 255, 255, 200],
            line_width_min_pixels=2,
        )
        capas.append(capa_nodos_camino)

        capa_texto = pdk.Layer(
            "TextLayer",
            data=nodos_camino,
            get_position=["lon", "lat"],
            get_text="name",
            get_size=12,
            get_color=COLOR_TEXTO,
            get_alignment_baseline="'bottom'",
            get_pixel_offset=[0, -20],
            pickable=False,
            billboard=True,
        )
        capas.append(capa_texto)

    return pdk.Deck(
        layers=capas,
        initial_view_state=VISTA_PERU,
        tooltip={
            "html": "<b>{algoritmo}</b>",
            "style": {
                "backgroundColor": "white",
                "color": "black",
            },
        },
        map_style="light",
    )
def _mostrar_leyenda_algoritmos(caminos_por_algoritmo: dict[str, list[str]]) -> None:
    """
    Muestra una leyenda visual con el color de cada algoritmo dibujado.
    """

    if not caminos_por_algoritmo:
        return

    html = '<div class="leyenda">'

    for algoritmo in caminos_por_algoritmo:
        color = COLORES_ALGORITMOS.get(algoritmo, [100, 100, 100, 220])
        rgb = f"rgb({color[0]}, {color[1]}, {color[2]})"

        html += (
            f'<span>'
            f'<span class="dot" style="background:{rgb}"></span>'
            f'{algoritmo}'
            f'</span>'
        )

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA  (debe ser la primera llamada Streamlit)
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="TINKUY",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Badges de nodos en la ruta */
    .path-badge {
        display: inline-block;
        background: #3b82f6;
        color: white;
        border-radius: 999px;
        padding: 2px 11px;
        margin: 2px 3px;
        font-size: 0.80em;
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    .badge-origen  { background: #f59e0b; color: #1c1c1c; }
    .badge-destino { background: #10b981; }

    /* Tarjeta de resultado por algoritmo */
    .algo-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .algo-card.winner {
        background: #f0fdf4;
        border-left-color: #10b981;
    }
    .algo-card.suboptimal {
        border-left-color: #f59e0b;
    }
    .algo-card.no-ruta {
        background: #fef2f2;
        border-left-color: #ef4444;
    }
    .algo-card h4 { margin: 0 0 6px 0; font-size: 0.95em; }
    .algo-card p  { margin: 0; font-size: 0.83em; color: #475569; }

    /* Leyenda del mapa */
    .leyenda {
        display: flex; gap: 18px; flex-wrap: wrap;
        font-size: 0.82em; color: #334155;
        margin-top: 6px;
    }
    .leyenda span { display: flex; align-items: center; gap: 5px; }
    .dot {
        width: 12px; height: 12px;
        border-radius: 50%; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

grafo, coords, nodos_df = _cargar_datos()
geojson_data             = _cargar_geojson()

DEPARTAMENTOS = get_departamentos()

DEP_LIMA = get_departamento("LIMA") or "LIMA"
DEP_PUNO = get_departamento("PUNO") or "PUNO"

# Opciones para seleccionar provincias en modo TSP.
# Se muestran como "DEPARTAMENTO / PROVINCIA" para mantener orden.
OPCIONES_TSP = []

for departamento in DEPARTAMENTOS:
    for provincia in get_provincias_por_departamento(departamento):
        OPCIONES_TSP.append(f"{departamento} / {provincia}")


MAPA_OPCION_PROVINCIA = {
    opcion: opcion.split(" / ", 1)[1]
    for opcion in OPCIONES_TSP
}


def _opcion_tsp_por_provincia(provincia: str) -> str | None:
    """
    Busca la opción visual correspondiente a una provincia.

    Ejemplo:
    "LIMA" -> "LIMA / LIMA"
    """
    departamento = get_departamento(provincia)

    if departamento is None:
        return None

    opcion = f"{departamento} / {provincia}"

    if opcion in OPCIONES_TSP:
        return opcion

    return None


DEFAULT_TSP = [
    opcion
    for opcion in [
        _opcion_tsp_por_provincia("LIMA"),
        _opcion_tsp_por_provincia("ICA"),
        _opcion_tsp_por_provincia("AREQUIPA"),
        _opcion_tsp_por_provincia("CUSCO"),
        _opcion_tsp_por_provincia("PUNO"),
    ]
    if opcion is not None
]

IDX_DEP_LIMA = _indice_defecto(DEPARTAMENTOS, [DEP_LIMA])
IDX_DEP_PUNO = _indice_defecto(DEPARTAMENTOS, [DEP_PUNO], fallback=min(1, len(DEPARTAMENTOS) - 1))

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — Panel de control
# ═══════════════════════════════════════════════════════════════════════════


with st.sidebar:
    

    st.markdown("## TINKUY")
    st.caption(f"{len(LISTA_PROVINCIAS)} provincias · {sum(len(v) for v in grafo.values())} aristas")

    st.divider()

    modo_trabajo = st.radio(
        "Modo de trabajo",
        options=[
            "Ruta corta",
            "Problema del Viajero (TSP)",
        ],
        index=0,
    )

    st.divider()

    # Valores por defecto para evitar errores entre modos
    buscar = False
    buscar_tsp = False

    provincias_tsp = []
    provincia_inicio_tsp = None
    volver_inicio_tsp = False
    algoritmos_tsp_seleccionados = {}

    origen = None
    destino = None
    algoritmos_seleccionados = {}

    # ─────────────────────────────────────────────────────────────────────
    # MODO 1: RUTA CORTA
    # ─────────────────────────────────────────────────────────────────────
    if modo_trabajo == "Ruta corta":
        st.markdown("#### 📍 Ruta")

        departamento_origen = st.selectbox(
            "Departamento de origen",
            options=DEPARTAMENTOS,
            index=IDX_DEP_LIMA,
            key="departamento_origen",
        )

        provincias_origen = get_provincias_por_departamento(departamento_origen)

        idx_prov_origen = _indice_defecto(
            provincias_origen,
            ["LIMA"],
            fallback=0,
        )

        origen = st.selectbox(
            "Provincia de origen",
            options=provincias_origen,
            index=idx_prov_origen,
            key="origen",
        )

        departamento_destino = st.selectbox(
            "Departamento de destino",
            options=DEPARTAMENTOS,
            index=IDX_DEP_PUNO,
            key="departamento_destino",
        )

        provincias_destino = get_provincias_por_departamento(departamento_destino)

        idx_prov_destino = _indice_defecto(
            provincias_destino,
            ["PUNO"],
            fallback=0,
        )

        destino = st.selectbox(
            "Provincia de destino",
            options=provincias_destino,
            index=idx_prov_destino,
            key="destino",
        )

        st.divider()

        st.markdown("#### ⚙️ Algoritmos")

        nombres_seleccionados: list[str] = st.multiselect(
            "Selecciona uno o más algoritmos",
            options=list(ALGORITMOS_DISPONIBLES.keys()),
            default=list(ALGORITMOS_DISPONIBLES.keys()),
            label_visibility="collapsed",
        )

        algoritmos_seleccionados = {
            n: ALGORITMOS_DISPONIBLES[n]
            for n in nombres_seleccionados
        }

        ady_origen = get_adyacentes(origen)
        ady_destino = get_adyacentes(destino)

        with st.expander(f"Vecinos de {origen} ({len(ady_origen)})", expanded=False):
            for prov, dist in sorted(ady_origen.items(), key=lambda x: x[1]):
                st.markdown(f"- **{prov}** — {dist:.1f} km")

        with st.expander(f"Vecinos de {destino} ({len(ady_destino)})", expanded=False):
            for prov, dist in sorted(ady_destino.items(), key=lambda x: x[1]):
                st.markdown(f"- **{prov}** — {dist:.1f} km")

        st.divider()

        buscar = st.button(
            "🚀 Calcular Ruta",
            use_container_width=True,
            type="primary",
            disabled=(origen == destino or not algoritmos_seleccionados),
        )

        if origen == destino:
            st.caption("⚠️ Origen y destino deben ser distintos.")
        elif not algoritmos_seleccionados:
            st.caption("⚠️ Selecciona al menos un algoritmo.")

    # ─────────────────────────────────────────────────────────────────────
    # MODO 2: PROBLEMA DEL VIAJERO
    # ─────────────────────────────────────────────────────────────────────
    elif modo_trabajo == "Problema del Viajero (TSP)":
        st.markdown("#### 🧭 Problema del Viajero")

        opciones_seleccionadas_tsp = st.multiselect(
            "Provincias a visitar",
            options=OPCIONES_TSP,
            default=DEFAULT_TSP,
            help="Formato: DEPARTAMENTO / PROVINCIA",
        )

        provincias_tsp = [
            MAPA_OPCION_PROVINCIA[opcion]
            for opcion in opciones_seleccionadas_tsp
        ]

        provincia_inicio_tsp = st.selectbox(
            "Provincia inicial",
            options=provincias_tsp if provincias_tsp else [],
            index=0 if provincias_tsp else None,
        )

        volver_inicio_tsp = st.checkbox(
            "Volver a la provincia inicial",
            value=False,
        )

        nombres_tsp_seleccionados = st.multiselect(
            "Algoritmos TSP",
            options=list(ALGORITMOS_TSP_DISPONIBLES.keys()),
            default=list(ALGORITMOS_TSP_DISPONIBLES.keys()),
        )

        algoritmos_tsp_seleccionados = {
            nombre: ALGORITMOS_TSP_DISPONIBLES[nombre]
            for nombre in nombres_tsp_seleccionados
        }

        valido_tsp, mensaje_tsp = validar_provincias_tsp(
            provincias_tsp,
            minimo=3,
            maximo=12,
        )

        buscar_tsp = st.button(
            "Calcular",
            use_container_width=True,
            type="primary",
            disabled=(
                not valido_tsp
                or not provincia_inicio_tsp
                or not algoritmos_tsp_seleccionados
            ),
        )

        if not valido_tsp:
            st.caption(f"⚠️ {mensaje_tsp}")
        elif not algoritmos_tsp_seleccionados:
            st.caption("⚠️ Selecciona al menos un algoritmo TSP.")

# ═══════════════════════════════════════════════════════════════════════════
# MODO PROBLEMA DEL VIAJERO — TSP
# ═══════════════════════════════════════════════════════════════════════════

if modo_trabajo == "Problema del Viajero (TSP)":

    if buscar_tsp:
        resultados_tsp: list[dict] = []
        barra_tsp = st.progress(0, text="Ejecutando algoritmos TSP…")

        coords_tsp = {
            provincia: get_coords(provincia)
            for provincia in provincias_tsp
        }

        for i, (nombre, funcion) in enumerate(algoritmos_tsp_seleccionados.items()):
            barra_tsp.progress(
                i / len(algoritmos_tsp_seleccionados),
                text=f"Ejecutando {nombre}…",
            )

            inicio = time.perf_counter()

            distancia, ruta = funcion(
                provincias=provincias_tsp,
                coords=coords_tsp,
                provincia_inicio=provincia_inicio_tsp,
                volver_inicio=volver_inicio_tsp,
            )

            tiempo_ms = (time.perf_counter() - inicio) * 1_000

            resultados_tsp.append(
                crear_resultado_tsp(
                    algoritmo=nombre,
                    ruta=ruta,
                    distancia=distancia,
                    tiempo_ms=tiempo_ms,
                )
            )

        barra_tsp.progress(1.0, text="✅ Listo")
        time.sleep(0.3)
        barra_tsp.empty()

        validos_tsp = [
            resultado
            for resultado in resultados_tsp
            if resultado["_distancia"] is not None
        ]

        mejor_tsp = (
         min(
             validos_tsp,
             key=lambda r: (
              round(r["_distancia"], 2),
              r["Tiempo (ms)"],
        ),
    )
    if validos_tsp
    else None
)

        st.session_state["resultados_tsp"] = resultados_tsp
        st.session_state["mejor_tsp"] = mejor_tsp
        st.session_state["camino_tsp"] = mejor_tsp["_ruta"] if mejor_tsp else None

    resultados_tsp = st.session_state.get("resultados_tsp", [])
    mejor_tsp = st.session_state.get("mejor_tsp", None)
    camino_tsp = st.session_state.get("camino_tsp", None)

    st.markdown("### 🧭 Problema del Viajero — TSP")

    st.caption(
        "El objetivo es visitar varias provincias buscando la menor distancia total."
    )

    tab_mapa_tsp, tab_tabla_tsp, tab_rendimiento_tsp = st.tabs(
        ["🗺️ Mapa TSP", "📊 Tabla Comparativa", "⏱️ Rendimiento"]
    )

    with tab_mapa_tsp:
        caminos_tsp = {
            r["Algoritmo"]: r["_ruta"]
            for r in resultados_tsp
            if r.get("_ruta")
        }

        _mostrar_leyenda_algoritmos(caminos_tsp)

        st.pydeck_chart(
            _construir_mapa_multiple(
                coords,
                nodos_df,
                geojson_data,
                caminos_tsp,
            ),
            use_container_width=True,
            height=560,
        )

        if mejor_tsp:
            st.markdown("---")
            st.markdown(f"#### 🏆 Mejor resultado — {mejor_tsp['Algoritmo']}")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "📏 Distancia total",
                f"{mejor_tsp['Distancia (km)']:,.2f} km",
            )

            c2.metric(
                "⏱️ Tiempo",
                f"{mejor_tsp['Tiempo (ms)']:.4f} ms",
            )

            c3.metric(
                "📍 Provincias",
                f"{mejor_tsp['Provincias']}",
            )

            if mejor_tsp["_ruta"]:
                st.markdown("**Secuencia de la ruta:**")
                st.markdown(" → ".join(mejor_tsp["_ruta"]))
    with tab_tabla_tsp:
        if not resultados_tsp:
            st.info("Ejecuta el cálculo TSP para ver los resultados.", icon="👈")
        else:
            distancia_base_tsp = mejor_tsp["_distancia"] if mejor_tsp else None

            resultados_tsp_ordenados = sorted(
                resultados_tsp,
                key=lambda r: (
                    round(r["_distancia"], 2) if r["_distancia"] is not None else float("inf"),
                    r["Tiempo (ms)"],
                ),
            )

            df_tsp = pd.DataFrame([
                {
                    "Algoritmo": r["Algoritmo"],
                    "Distancia (km)": r["Distancia (km)"] if r["Distancia (km)"] is not None else "—",
                    "Provincias": r["Provincias"] if r["Provincias"] is not None else "—",
                    "Tiempo (ms)": r["Tiempo (ms)"],
                    "Exceso (km)": (
                        round(r["_distancia"] - distancia_base_tsp, 2)
                        if r["_distancia"] is not None and distancia_base_tsp is not None
                        else "—"
                    ),
                    "Exceso (%)": (
                        f"{((r['_distancia'] - distancia_base_tsp) / distancia_base_tsp) * 100:.2f}%"
                        if r["_distancia"] is not None and distancia_base_tsp
                        else "—"
                    ),
                    "Mejor": "🏆" if mejor_tsp and r["Algoritmo"] == mejor_tsp["Algoritmo"] else "",
                }
                for r in resultados_tsp_ordenados
            ])

            st.dataframe(
                df_tsp,
                use_container_width=True,
                hide_index=True,
            )   
    with tab_rendimiento_tsp:
        if not resultados_tsp:
            st.info("Ejecuta el cálculo TSP para ver el rendimiento.", icon="👈")
        else:
            df_tiempo_tsp = pd.DataFrame({
                "Algoritmo": [r["Algoritmo"] for r in resultados_tsp],
                "Tiempo (ms)": [r["Tiempo (ms)"] for r in resultados_tsp],
            }).set_index("Algoritmo")

            st.markdown("#### ⏱️ Tiempo de ejecución")
            st.bar_chart(df_tiempo_tsp)

            validos_dist_tsp = [
                r for r in resultados_tsp
                if r["_distancia"] is not None
            ]

            if validos_dist_tsp:
                df_dist_tsp = pd.DataFrame({
                    "Algoritmo": [r["Algoritmo"] for r in validos_dist_tsp],
                    "Distancia (km)": [r["Distancia (km)"] for r in validos_dist_tsp],
                }).set_index("Algoritmo")

                st.markdown("#### 📏 Distancia encontrada")
                st.bar_chart(df_dist_tsp)

    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DE ALGORITMOS (al pulsar el botón)
# ═══════════════════════════════════════════════════════════════════════════

if buscar:
    resultados: list[dict] = []
    barra = st.progress(0, text="Ejecutando algoritmos…")

    for i, (nombre, func) in enumerate(algoritmos_seleccionados.items()):
        barra.progress((i) / len(algoritmos_seleccionados), text=f"Ejecutando {nombre}…")
        inicio    = time.perf_counter()
        dist, cam = func(grafo, origen, destino, coords)
        elapsed   = (time.perf_counter() - inicio) * 1_000

        resultados.append({
            "Algoritmo":      nombre,
            "Distancia (km)": round(dist, 2)  if dist is not None else None,
            "Pasos":          len(cam) - 1    if cam  is not None else None,
            "Tiempo (ms)":    round(elapsed, 4),
            "_camino":        cam,
            "_distancia":     dist,
        })

    barra.progress(1.0, text="✅ Listo")
    time.sleep(0.3)
    barra.empty()

    # Mejor resultado: menor distancia entre los válidos
    validos = [r for r in resultados if r["_distancia"] is not None]

    mejor = (
        min(
            validos,
            key=lambda r: (
                round(r["_distancia"], 2),
                r["Tiempo (ms)"],
            ),
        )
        if validos
        else None
    )

    # Persistir en session_state para que los tabs lo lean
    st.session_state["resultados"]  = resultados
    st.session_state["mejor"]       = mejor
    st.session_state["camino_mapa"] = mejor["_camino"] if mejor else None


# Recuperar estado de forma segura
resultados = st.session_state.get("resultados", [])
mejor = st.session_state.get("mejor", None)
camino_mapa = st.session_state.get("camino_mapa", None)

# ═══════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL — Tabs
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f"### `{departamento_origen} / {origen}` → `{departamento_destino} / {destino}`"
)

tab_mapa, tab_tabla, tab_rendimiento = st.tabs(
    ["🗺️ Mapa Interactivo", "📊 Tabla Comparativa", "⏱️ Rendimiento"]
)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — MAPA INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════════

with tab_mapa:

    # Leyenda del mapa
    if geojson_data is None:
        st.info(
            "ℹ️ `peru_provincial_simple.geojson` no encontrado. "
            "El GeoJsonLayer de fondo no se mostrará, pero el resto funciona correctamente.",
            icon="📂",
        )

    st.markdown("""
    <div class="leyenda">
        <span><span class="dot" style="background:#f59e0b"></span> Origen</span>
        <span><span class="dot" style="background:#10b981"></span> Destino</span>
        <span><span class="dot" style="background:#3b82f6"></span> Nodo intermedio</span>
        <span><span class="dot" style="background:#ef4444"></span> Ruta óptima</span>
        <span><span class="dot" style="background:#a0aab4"></span> Todas las provincias</span>
    </div>
    """, unsafe_allow_html=True)

    caminos_ruta_corta = {
           r["Algoritmo"]: r["_camino"]
           for r in resultados
           if r.get("_camino")
           }

    _mostrar_leyenda_algoritmos(caminos_ruta_corta)

    st.pydeck_chart(
        _construir_mapa_multiple(
            coords,
            nodos_df,
            geojson_data,
            caminos_ruta_corta,
        ),
        use_container_width=True,
        height=560,
    )

    # Métricas del ganador (bajo el mapa)
    if mejor:
        st.markdown("---")
        st.markdown(f"#### 🏆 Mejor resultado — {mejor['Algoritmo']}")
        mc1, mc2, mc3 = st.columns(3)

        dist_ref = mejor["Distancia (km)"]
        # Delta contra el peor válido
        peor_dist = max(
            (r["_distancia"] for r in resultados if r["_distancia"] is not None),
            default=dist_ref,
        )

        mc1.metric(
            label="📏 Distancia Total",
            value=f"{dist_ref:,.2f} km",
            delta=f"{dist_ref - peor_dist:+.2f} km vs peor",
            delta_color="inverse",
        )
        mc2.metric(
            label="⏱️ Tiempo de Ejecución",
            value=f"{mejor['Tiempo (ms)']:.4f} ms",
        )
        mc3.metric(
            label="🔢 Nodos Recorridos",
            value=f"{mejor['Pasos']} pasos",
        )

        # Secuencia de nodos del camino
        if mejor["_camino"]:
            st.markdown("**Secuencia de la ruta óptima:**")
            badges = []
            for i, p in enumerate(mejor["_camino"]):
                if i == 0:
                    cls = "path-badge badge-origen"
                elif i == len(mejor["_camino"]) - 1:
                    cls = "path-badge badge-destino"
                else:
                    cls = "path-badge"
                badges.append(f'<span class="{cls}">{p}</span>')
            st.markdown(" → ".join(badges), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — TABLA COMPARATIVA
# ═══════════════════════════════════════════════════════════════════════════

with tab_tabla:
    if not resultados:
        st.info("Ejecuta una búsqueda para ver los resultados.", icon="👈")
    else:
        # ── Tarjetas por algoritmo ───────────────────────────────────────────
        dist_optima = mejor["_distancia"] if mejor else None

        resultados_ordenados = sorted(
            resultados,
            key=lambda r: (
                round(r["_distancia"], 2) if r["_distancia"] is not None else float("inf"),
                r["Tiempo (ms)"],
            ),
        )

        for r in resultados_ordenados:
            cam      = r["_camino"]
            dist_r   = r["_distancia"]
            es_mejor = mejor and r["Algoritmo"] == mejor["Algoritmo"]

            if dist_r is None:
                css_card = "algo-card no-ruta"
                icon     = "❌"
            elif es_mejor:
                css_card = "algo-card winner"
                icon     = "🏆"
            elif dist_optima and dist_r > dist_optima * 1.001:
                css_card = "algo-card suboptimal"
                icon     = "⚠️"
            else:
                css_card = "algo-card"
                icon     = "✅"

            if cam:
                badges = " → ".join(
                    f'<span class="path-badge'
                    + (" badge-origen" if j == 0 else " badge-destino" if j == len(cam) - 1 else "")
                    + f'">{p}</span>'
                    for j, p in enumerate(cam)
                )
                detalle = (
                    f"{r['Distancia (km)']} km · "
                    f"{r['Pasos']} pasos · "
                    f"{r['Tiempo (ms)']} ms"
                )
                contenido = (
                    f'<div class="{css_card}">'
                    f'<h4>{icon} {r["Algoritmo"]}</h4>'
                    f'<p>{detalle}</p>'
                    f'<p style="margin-top:6px">{badges}</p>'
                    f'</div>'
                )
            else:
                contenido = (
                    f'<div class="{css_card}">'
                    f'<h4>{icon} {r["Algoritmo"]}</h4>'
                    f'<p>Sin ruta encontrada · {r["Tiempo (ms)"]} ms</p>'
                    f'</div>'
                )

            st.markdown(contenido, unsafe_allow_html=True)

        # ── DataFrame completo (expandible) ─────────────────────────────────
        with st.expander("Ver tabla de datos completa"):
            resultados_ordenados = sorted(
                resultados,
                key=lambda r: (
                    round(r["_distancia"], 2) if r["_distancia"] is not None else float("inf"),
                    r["Tiempo (ms)"],
                ),
            )

            df_display = pd.DataFrame([
                {
                    "Algoritmo": r["Algoritmo"],
                    "Distancia (km)": r["Distancia (km)"] if r["Distancia (km)"] is not None else "—",
                    "Pasos": r["Pasos"] if r["Pasos"] is not None else "—",
                    "Tiempo (ms)": r["Tiempo (ms)"],
                    "Óptimo": "🏆" if (mejor and r["Algoritmo"] == mejor["Algoritmo"]) else "",
                }
                for r in resultados_ordenados
            ])

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — RENDIMIENTO
# ═══════════════════════════════════════════════════════════════════════════

with tab_rendimiento:
    if not resultados:
        st.info("Ejecuta una búsqueda para ver el análisis de rendimiento.", icon="👈")
    else:
        # ── Métricas de todos los algoritmos en columnas ─────────────────────
        st.markdown("#### Métricas por algoritmo")
        cols_metr = st.columns(min(len(resultados), 4))
        for i, r in enumerate(resultados):
            col = cols_metr[i % len(cols_metr)]
            with col:
                es_ganador = mejor and r["Algoritmo"] == mejor["Algoritmo"]
                label_t    = f"{'🏆 ' if es_ganador else ''}{r['Algoritmo']}"
                st.metric(label=label_t, value=f"{r['Tiempo (ms)']:.4f} ms")

        st.divider()

        # ── Gráfico de barras: tiempos ───────────────────────────────────────
        st.markdown("#### ⏱️ Tiempo de ejecución (ms)")
        df_tiempo = pd.DataFrame({
            "Algoritmo":   [r["Algoritmo"]   for r in resultados],
            "Tiempo (ms)": [r["Tiempo (ms)"] for r in resultados],
        }).set_index("Algoritmo")
        st.bar_chart(df_tiempo, color="#3b82f6")

        st.divider()

        # ── Gráfico de barras: distancias ────────────────────────────────────
        validos_dist = [r for r in resultados if r["_distancia"] is not None]
        if validos_dist:
            st.markdown("#### 📏 Distancia encontrada (km)")
            df_dist = pd.DataFrame({
                "Algoritmo":      [r["Algoritmo"]      for r in validos_dist],
                "Distancia (km)": [r["Distancia (km)"] for r in validos_dist],
            }).set_index("Algoritmo")
            st.bar_chart(df_dist, color="#10b981")

        st.divider()

        # ── Análisis de suboptimalidad ────────────────────────────────────────
        if mejor and len(validos_dist) > 1:
            st.markdown("#### 🔍 Análisis de suboptimalidad")
            dist_opt = mejor["_distancia"]
            filas = []
            for r in validos_dist:
                exceso = r["_distancia"] - dist_opt
                exceso_pct = (exceso / dist_opt) * 100 if dist_opt > 0 else 0
                filas.append({
                    "Algoritmo":        r["Algoritmo"],
                    "Distancia (km)":   r["Distancia (km)"],
                    "Exceso vs óptimo": f"+{exceso:.2f} km" if exceso > 0.01 else "—",
                    "Exceso (%)":       f"+{exceso_pct:.2f}%" if exceso > 0.01 else "—",
                    "Es óptimo":        "✅" if exceso <= 0.01 else "⚠️",
                })
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.divider()
st.caption("Proyecto TINKUY · Algoritmos de Ruta Corta · Provincias del Perú")
