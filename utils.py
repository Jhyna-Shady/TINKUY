# utils.py
# Utilidades compartidas por todos los algoritmos de ruta corta

import math


# ---------------------------------------------------------------------------
# Fórmula de Haversine
# ---------------------------------------------------------------------------
_R = 6_371.0  # Radio medio de la Tierra en km


def haversine(coords1: tuple[float, float], coords2: tuple[float, float]) -> float:
    """
    Distancia en línea recta (km) entre dos puntos dados como (lat, lon) en grados.
    Usada como heurística admisible en A* y Greedy BFS.
    """
    lat1, lon1 = math.radians(coords1[0]), math.radians(coords1[1])
    lat2, lon2 = math.radians(coords2[0]), math.radians(coords2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return _R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Reconstrucción de camino a partir de un dict de predecesores
# ---------------------------------------------------------------------------
def reconstruir_camino(previo: dict[str, str | None], origen: str, destino: str) -> list[str] | None:
    """
    Recorre el dict {nodo: nodo_previo} desde `destino` hasta `origen`.
    Retorna la lista de nodos en orden origen → destino, o None si no hay ruta.
    """
    if destino not in previo:
        return None

    camino, actual = [], destino
    while actual is not None:
        camino.append(actual)
        actual = previo.get(actual)

    camino.reverse()
    return camino if camino[0] == origen else None
