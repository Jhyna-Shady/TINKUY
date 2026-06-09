# a_star.py
# Algoritmo A* (A-estrella) — búsqueda informada con heurística admisible
#
# Complejidad: O(E log V) en el caso promedio con buena heurística.
# La heurística Haversine es admisible porque la distancia en línea recta
# nunca sobreestima la distancia real por carretera.

import heapq
from utils import haversine, reconstruir_camino


def astar(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,
) -> tuple[float | None, list[str] | None]:
    """
    Encuentra la ruta de menor distancia usando A* con heurística Haversine.

    Parámetros
    ----------
    grafo   : {nodo: {vecino: peso_km}}
    origen  : nodo de partida
    destino : nodo de llegada
    coords  : {nodo: (lat, lon)} — requerido para la heurística

    Retorna
    -------
    (distancia_total_km, lista_de_nodos) o (None, None) si no hay ruta.
    """
    if origen not in grafo or destino not in grafo:
        return None, None

    if coords is None:
        coords = {}

    def h(nodo: str) -> float:
        """Heurística: distancia Haversine al destino."""
        if nodo in coords and destino in coords:
            return haversine(coords[nodo], coords[destino])
        return 0.0  # degradar a Dijkstra si faltan coordenadas

    # g[n] = coste real acumulado desde origen hasta n
    g      = {nodo: float("inf") for nodo in grafo}
    previo = {nodo: None         for nodo in grafo}
    g[origen] = 0.0

    # heap: (f = g + h, nodo)
    heap = [(h(origen), origen)]

    while heap:
        f_actual, nodo = heapq.heappop(heap)

        if nodo == destino:
            break

        # Descarte de entradas obsoletas
        if f_actual > g[nodo] + h(nodo):
            continue

        for vecino, peso in grafo[nodo].items():
            nuevo_g = g[nodo] + peso
            if nuevo_g < g[vecino]:
                g[vecino]      = nuevo_g
                previo[vecino] = nodo
                heapq.heappush(heap, (nuevo_g + h(vecino), vecino))

    if g[destino] == float("inf"):
        return None, None

    camino = reconstruir_camino(previo, origen, destino)
    return g[destino], camino
