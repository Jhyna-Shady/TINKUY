"""
tsp_utils.py

Funciones auxiliares para el Problema del Viajero (TSP).

Este archivo no contiene un algoritmo TSP específico.
Solo contiene funciones comunes que serán usadas por:
- vecino_cercano.py
- fuerza_bruta.py
- dfs_poda.py
- bfs_poda.py
- astar_tsp.py
- two_opt.py
- algoritmo_genetico.py
"""

from math import radians, sin, cos, sqrt, atan2
from typing import Any


def distancia_haversine(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calcula la distancia aproximada en kilómetros entre dos puntos geográficos.

    Usa la fórmula de Haversine, que sirve para calcular distancias
    considerando la curvatura de la Tierra.

    Parámetros:
    - lat1, lon1: latitud y longitud del primer punto.
    - lat2, lon2: latitud y longitud del segundo punto.

    Retorna:
    - Distancia en kilómetros.
    """

    radio_tierra_km = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return radio_tierra_km * c


def obtener_distancia(
    provincia_a: str,
    provincia_b: str,
    coords: dict[str, tuple[float, float]],
) -> float:
    """
    Obtiene la distancia entre dos provincias usando sus coordenadas.

    Parámetros:
    - provincia_a: nombre de la primera provincia.
    - provincia_b: nombre de la segunda provincia.
    - coords: diccionario con coordenadas de provincias.

    Ejemplo de coords:
    {
        "LIMA": (-12.0464, -77.0428),
        "PUNO": (-15.8402, -70.0219)
    }

    Retorna:
    - Distancia en kilómetros.
    """

    if provincia_a not in coords:
        raise ValueError(f"No se encontraron coordenadas para {provincia_a}")

    if provincia_b not in coords:
        raise ValueError(f"No se encontraron coordenadas para {provincia_b}")

    lat1, lon1 = coords[provincia_a]
    lat2, lon2 = coords[provincia_b]

    if None in (lat1, lon1, lat2, lon2):
        raise ValueError(
            f"Coordenadas inválidas entre {provincia_a} y {provincia_b}"
        )

    return distancia_haversine(lat1, lon1, lat2, lon2)


def calcular_distancia_total(
    ruta: list[str],
    coords: dict[str, tuple[float, float]],
    volver_inicio: bool = False,
) -> float:
    """
    Calcula la distancia total de una ruta.

    Parámetros:
    - ruta: lista ordenada de provincias.
    - coords: coordenadas de las provincias.
    - volver_inicio: si es True, agrega el tramo final hacia la primera provincia.

    Ejemplo sin volver al inicio:
    LIMA → ICA → AREQUIPA

    Ejemplo con volver al inicio:
    LIMA → ICA → AREQUIPA → LIMA

    Retorna:
    - Distancia total en kilómetros.
    """

    if not ruta or len(ruta) < 2:
        return 0.0

    distancia_total = 0.0

    for i in range(len(ruta) - 1):
        distancia_total += obtener_distancia(
            ruta[i],
            ruta[i + 1],
            coords,
        )

    if volver_inicio:
        distancia_total += obtener_distancia(
            ruta[-1],
            ruta[0],
            coords,
        )

    return distancia_total


def construir_matriz_distancias(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
) -> dict[str, dict[str, float]]:
    """
    Construye una matriz de distancias entre todas las provincias seleccionadas.

    Ejemplo de retorno:
    {
        "LIMA": {
            "ICA": 265.4,
            "CUSCO": 572.8
        },
        "ICA": {
            "LIMA": 265.4,
            "CUSCO": 480.2
        }
    }

    Esta matriz ayuda a que los algoritmos TSP no calculen la misma distancia
    muchas veces.
    """

    matriz = {}

    for provincia_a in provincias:
        matriz[provincia_a] = {}

        for provincia_b in provincias:
            if provincia_a == provincia_b:
                matriz[provincia_a][provincia_b] = 0.0
            else:
                matriz[provincia_a][provincia_b] = obtener_distancia(
                    provincia_a,
                    provincia_b,
                    coords,
                )

    return matriz


def distancia_en_matriz(
    matriz: dict[str, dict[str, float]],
    provincia_a: str,
    provincia_b: str,
) -> float:
    """
    Obtiene la distancia entre dos provincias desde una matriz ya calculada.

    Esto evita recalcular distancias varias veces.
    """

    return matriz[provincia_a][provincia_b]


def calcular_distancia_total_matriz(
    ruta: list[str],
    matriz: dict[str, dict[str, float]],
    volver_inicio: bool = False,
) -> float:
    """
    Calcula la distancia total de una ruta usando una matriz de distancias.

    Es más eficiente que calcular la distancia con Haversine en cada paso.
    """

    if not ruta or len(ruta) < 2:
        return 0.0

    distancia_total = 0.0

    for i in range(len(ruta) - 1):
        distancia_total += matriz[ruta[i]][ruta[i + 1]]

    if volver_inicio:
        distancia_total += matriz[ruta[-1]][ruta[0]]

    return distancia_total


def validar_provincias_tsp(
    provincias: list[str],
    minimo: int = 3,
    maximo: int | None = None,
) -> tuple[bool, str]:
    """
    Valida si la lista de provincias es adecuada para resolver el TSP.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - minimo: cantidad mínima de provincias.
    - maximo: cantidad máxima permitida.

    Retorna:
    - True o False.
    - Mensaje explicativo.
    """

    if not provincias:
        return False, "Debes seleccionar provincias."

    provincias_unicas = list(dict.fromkeys(provincias))

    if len(provincias_unicas) < minimo:
        return False, f"Debes seleccionar al menos {minimo} provincias."

    if maximo is not None and len(provincias_unicas) > maximo:
        return False, f"Debes seleccionar como máximo {maximo} provincias."

    return True, "Selección válida."


def crear_resultado_tsp(
    algoritmo: str,
    ruta: list[str] | None,
    distancia: float | None,
    tiempo_ms: float,
) -> dict[str, Any]:
    """
    Estandariza el resultado de cualquier algoritmo TSP.

    Esto permite que todos los algoritmos devuelvan la misma estructura.

    Retorna:
    {
        "Algoritmo": "Vecino más cercano",
        "Distancia (km)": 1234.56,
        "Provincias": 5,
        "Tiempo (ms)": 0.25,
        "_ruta": [...],
        "_distancia": 1234.56
    }
    """

    return {
        "Algoritmo": algoritmo,
        "Distancia (km)": round(distancia, 2) if distancia is not None else None,
        "Provincias": len(ruta) if ruta else None,
        "Tiempo (ms)": round(tiempo_ms, 4),
        "_ruta": ruta,
        "_distancia": distancia,
    }