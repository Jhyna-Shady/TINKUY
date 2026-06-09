"""
data.py  (refactorizado)
========================
Adaptador (wrapper) entre grafo_completo.json y el resto de la aplicación.

Ya NO contiene datos hardcodeados.  Lee grafo_completo.json generado por
generar_grafo.py y expone exactamente la misma API pública que antes:

    LISTA_PROVINCIAS          → list[str]  ordenada alfabéticamente
    get_grafo()               → dict[str, dict[str, float]]
    get_adyacentes(provincia) → dict[str, float]
    get_coords(provincia)     → tuple[float, float]   (lat, lon)

Los 7 algoritmos y app.py no requieren ninguna modificación.
"""

import json
import sys
from pathlib import Path
from functools import lru_cache

# ---------------------------------------------------------------------------
# Ruta al JSON generado por generar_grafo.py
# ---------------------------------------------------------------------------
_JSON_PATH = Path(__file__).parent / "grafo_completo.json"


# ---------------------------------------------------------------------------
# Carga única del JSON (lazy + cacheada)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _cargar_datos() -> dict:
    """
    Lee grafo_completo.json una sola vez y lo mantiene en memoria.
    Lanza un error claro si el archivo no existe, para guiar al usuario.
    """
    if not _JSON_PATH.exists():
        print(
            "\n❌  No se encontró 'grafo_completo.json'.\n"
            "    Ejecuta primero el script de preprocesamiento:\n\n"
            "        python generar_grafo.py\n",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(_JSON_PATH, encoding="utf-8") as f:
        datos = json.load(f)

    return datos


# ---------------------------------------------------------------------------
# API pública — misma interfaz que el data.py anterior
# ---------------------------------------------------------------------------
def get_grafo() -> dict[str, dict[str, float]]:
    """
    Retorna el grafo completo como {nodo: {vecino: peso_km}}.
    Firma idéntica al data.py anterior.
    """
    datos = _cargar_datos()
    return {provincia: info["adyacentes"] for provincia, info in datos.items()}


def get_adyacentes(provincia: str) -> dict[str, float]:
    """
    Retorna {vecino: distancia_km} para la provincia dada.
    Retorna {} si la provincia no existe en el grafo.
    """
    datos = _cargar_datos()
    return datos.get(provincia, {}).get("adyacentes", {})


def get_coords(provincia: str) -> tuple[float, float]:
    """
    Retorna (lat, lon) del centroide de la provincia.
    Retorna (None, None) si la provincia no existe.
    """
    datos = _cargar_datos()
    info  = datos.get(provincia, {})
    lat   = info.get("lat")
    lon   = info.get("lon")
    return (lat, lon)


def get_departamento(provincia: str) -> str | None:
    """
    Nuevo helper: retorna el nombre del departamento al que pertenece la provincia.
    No estaba en el data.py anterior; disponible opcionalmente para la UI.
    """
    datos = _cargar_datos()
    return datos.get(provincia, {}).get("departamento")

def get_mapa_departamento_provincias() -> dict[str, list[str]]:
    """
    Retorna un diccionario con esta estructura:

    {
        "LIMA": ["BARRANCA", "CAJATAMBO", "CANTA", "LIMA", ...],
        "PUNO": ["AZANGARO", "CARABAYA", "CHUCUITO", ...]
    }

    Sirve para organizar las provincias por departamento en la interfaz.
    """
    datos = _cargar_datos()
    mapa = {}

    for provincia, info in datos.items():
        departamento = info.get("departamento", "SIN DEPARTAMENTO")
        mapa.setdefault(departamento, []).append(provincia)

    return {
        departamento: sorted(provincias)
        for departamento, provincias in sorted(mapa.items())
    }


def get_departamentos() -> list[str]:
    """
    Retorna la lista ordenada de departamentos.
    """
    return sorted(get_mapa_departamento_provincias().keys())


def get_provincias_por_departamento(departamento: str) -> list[str]:
    """
    Retorna las provincias que pertenecen a un departamento.
    """
    mapa = get_mapa_departamento_provincias()
    return mapa.get(departamento, [])

# ---------------------------------------------------------------------------
# Lista ordenada de provincias — usada por los dropdowns de Streamlit
# ---------------------------------------------------------------------------
# Se evalúa en tiempo de importación; si el JSON no existe, falla aquí
# con el mensaje claro de _cargar_datos().
LISTA_PROVINCIAS: list[str] = sorted(_cargar_datos().keys())
