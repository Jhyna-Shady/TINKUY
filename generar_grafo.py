"""
generar_grafo.py
================
Script de preprocesamiento (ejecutar UNA VEZ antes de levantar la app).

Flujo:
  peru_provincial_simple.geojson
        │
        ├─ Leer con geopandas
        ├─ Calcular centroides (CRS WGS-84 → UTM 18S → centroide → WGS-84)
        ├─ Detectar colindancias (buffer 1 m + sjoin intersects)
        ├─ Calcular distancias entre centroides con Haversine
        └─ Exportar  grafo_completo.json

Salida esperada:
  {
    "ABANCAY": {
      "lat": -13.756,
      "lon": -72.881,
      "departamento": "APURIMAC",
      "adyacentes": {
        "ANDAHUAYLAS": 123.4,
        "AYMARAES":     87.2,
        ...
      }
    },
    ...
  }

Uso:
  python generar_grafo.py
  python generar_grafo.py --geojson ruta/otro.geojson --salida otro_grafo.json
"""

import argparse
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd


# ---------------------------------------------------------------------------
# Configuración por defecto
# ---------------------------------------------------------------------------
GEOJSON_DEFAULT = "peru_provincial_simple.geojson"
SALIDA_DEFAULT  = "grafo_completo.json"

# CRS proyectado para Perú — UTM Zona 18S (EPSG:32718)
# Necesario para que los centroides sean geométricamente correctos
# y el buffer de 1 m tenga sentido métrico.
CRS_PROJ = "EPSG:32718"
CRS_GEO  = "EPSG:4326"

# Campo de nombre de provincia en el GeoJSON del IGN
CAMPO_NOMBRE = "NOMBPROV"
CAMPO_DPTO   = "FIRST_NOMB"

# Buffer en metros para detectar colindancias (tolera pequeñas brechas
# entre polígonos que deberían tocarse pero no lo hacen exactamente
# por simplificación geométrica del shapefile).
BUFFER_M = 50


# ---------------------------------------------------------------------------
# Fórmula de Haversine (autocontenida — no depende de utils.py)
# ---------------------------------------------------------------------------
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en km entre dos puntos (lat/lon en grados decimales)."""
    R = 6_371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a  = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return round(R * 2 * math.asin(math.sqrt(a)), 4)


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def generar_grafo(geojson_path: str, salida_path: str) -> dict:
    """
    Lee el GeoJSON, detecta colindancias y exporta el grafo como JSON.
    Retorna el dict del grafo para uso programático.
    """

    # ── 1. Cargar GeoJSON ───────────────────────────────────────────────────
    print(f"[1/5] Leyendo {geojson_path} …")
    ruta = Path(geojson_path)
    if not ruta.exists():
        print(f"ERROR: no se encontró el archivo '{geojson_path}'.")
        print("       Colócalo en el mismo directorio o usa --geojson <ruta>.")
        sys.exit(1)

    gdf = gpd.read_file(geojson_path)
    n_total = len(gdf)
    print(f"       {n_total} features cargadas.")

    # Validar columnas requeridas
    for col in (CAMPO_NOMBRE, CAMPO_DPTO):
        if col not in gdf.columns:
            cols = list(gdf.columns)
            print(f"ERROR: columna '{col}' no encontrada. Columnas disponibles: {cols}")
            sys.exit(1)

    # Normalizar nombres: strip + upper para evitar duplicados por espacio/casing
    gdf[CAMPO_NOMBRE] = gdf[CAMPO_NOMBRE].str.strip().str.upper()
    gdf[CAMPO_DPTO]   = gdf[CAMPO_DPTO].str.strip().str.upper()

    # Eliminar duplicados de nombre (quedarse con el primer polígono)
    n_antes = len(gdf)
    gdf = gdf.drop_duplicates(subset=CAMPO_NOMBRE, keep="first").reset_index(drop=True)
    if len(gdf) < n_antes:
        print(f"       ⚠  {n_antes - len(gdf)} duplicados eliminados.")

    # ── 2. Calcular centroides en WGS-84 ────────────────────────────────────
    print("[2/5] Calculando centroides …")
    gdf_geo  = gdf.set_crs(CRS_GEO, allow_override=True) if gdf.crs is None else gdf.to_crs(CRS_GEO)
    gdf_proj = gdf_geo.to_crs(CRS_PROJ)

    centroides_proj = gdf_proj.geometry.centroid          # en metros
    centroides_geo  = centroides_proj.to_crs(CRS_GEO)    # de vuelta a lat/lon

    gdf_proj["centroid_lat"] = centroides_geo.y
    gdf_proj["centroid_lon"] = centroides_geo.x
    gdf_proj[CAMPO_NOMBRE]   = gdf[CAMPO_NOMBRE].values
    gdf_proj[CAMPO_DPTO]     = gdf[CAMPO_DPTO].values

    # ── 3. Detectar colindancias por buffer + sjoin ──────────────────────────
    print(f"[3/5] Detectando colindancias (buffer={BUFFER_M} m) …")
    gdf_buff = gdf_proj.copy()
    gdf_buff["geometry"] = gdf_proj.geometry.buffer(BUFFER_M)

    # sjoin: cada polígono con buffer intersecta a sus vecinos
    join = gpd.sjoin(
        gdf_buff[[CAMPO_NOMBRE, CAMPO_DPTO, "centroid_lat", "centroid_lon", "geometry"]],
        gdf_buff[[CAMPO_NOMBRE, "centroid_lat", "centroid_lon", "geometry"]],
        how="inner",
        predicate="intersects",
        lsuffix="left",
        rsuffix="right",
    )

    # Eliminar auto-referencias (un polígono consigo mismo)
    join = join[join[f"{CAMPO_NOMBRE}_left"] != join[f"{CAMPO_NOMBRE}_right"]].copy()

    n_aristas = len(join)
    print(f"       {n_aristas} pares colindantes detectados (antes de deduplicar).")

    # ── 4. Calcular distancias Haversine entre centroides ───────────────────
    print("[4/5] Calculando distancias Haversine …")
    join["distancia_km"] = join.apply(
        lambda row: haversine(
            row["centroid_lat_left"],
            row["centroid_lon_left"],
            row["centroid_lat_right"],
            row["centroid_lon_right"],
        ),
        axis=1,
    )

    # ── 5. Construir dict del grafo y exportar JSON ──────────────────────────
    print("[5/5] Construyendo grafo y exportando JSON …")

    # Índice de metadatos por provincia
    meta: dict[str, dict] = {}
    for _, row in gdf_proj.iterrows():
        nombre = row[CAMPO_NOMBRE]
        meta[nombre] = {
            "lat":          round(row["centroid_lat"], 6),
            "lon":          round(row["centroid_lon"], 6),
            "departamento": row[CAMPO_DPTO],
            "adyacentes":   {},
        }

    # Rellenar adyacentes
    for _, row in join.iterrows():
        origen_  = row[f"{CAMPO_NOMBRE}_left"]
        destino_ = row[f"{CAMPO_NOMBRE}_right"]
        dist_km  = row["distancia_km"]

        if origen_ in meta:
            # Conservar la menor distancia si hay duplicados por buffer overlap
            existente = meta[origen_]["adyacentes"].get(destino_, float("inf"))
            meta[origen_]["adyacentes"][destino_] = min(existente, dist_km)

    # Ordenar adyacentes por distancia (legibilidad)
    for nombre in meta:
        meta[nombre]["adyacentes"] = dict(
            sorted(meta[nombre]["adyacentes"].items(), key=lambda x: x[1])
        )

    # Exportar
    Path(salida_path).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    n_provincias = len(meta)
    n_aristas_fin = sum(len(v["adyacentes"]) for v in meta.values())
    print(f"\n✅ grafo_completo.json generado:")
    print(f"   · {n_provincias} provincias")
    print(f"   · {n_aristas_fin} aristas dirigidas ({n_aristas_fin // 2} conexiones únicas)")
    print(f"   · Guardado en: {Path(salida_path).resolve()}")

    return meta


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera grafo_completo.json a partir del GeoJSON provincial del Perú."
    )
    parser.add_argument(
        "--geojson",
        default=GEOJSON_DEFAULT,
        help=f"Ruta al GeoJSON de entrada (default: {GEOJSON_DEFAULT})",
    )
    parser.add_argument(
        "--salida",
        default=SALIDA_DEFAULT,
        help=f"Ruta del JSON de salida (default: {SALIDA_DEFAULT})",
    )
    args = parser.parse_args()

    generar_grafo(args.geojson, args.salida)
