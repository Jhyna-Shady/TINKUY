# dijkstra.py
# Algoritmo de Dijkstra — ruta de menor coste en grafos con pesos no negativos
#
# Complejidad: O((V + E) log V) con min-heap
# Garantiza optimalidad siempre que todos los pesos sean >= 0.

import heapq
from utils import reconstruir_camino


def dijkstra(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,   # ignorado; firma uniforme
) -> tuple[float | None, list[str] | None]:
    """
    Encuentra la ruta de menor distancia entre `origen` y `destino`.

    Parámetros
    ----------
    grafo   : {nodo: {vecino: peso_km}}
    origen  : nodo de partida
    destino : nodo de llegada
    coords  : no utilizado (se acepta para mantener firma uniforme con A*)

    Retorna
    -------
    (distancia_total_km, lista_de_nodos) o (None, None) si no hay ruta.
    """
    if origen not in grafo or destino not in grafo:
        return None, None

    # dist[n] = menor distancia conocida desde origen hasta n
    dist    = {nodo: float("inf") for nodo in grafo}
    previo  = {nodo: None         for nodo in grafo}
    dist[origen] = 0.0

    # heap: (distancia_acumulada, nodo)
    heap = [(0.0, origen)]

    while heap:
        d_actual, nodo = heapq.heappop(heap)

        # Nodo ya procesado con mejor coste → ignorar
        if d_actual > dist[nodo]:
            continue

        if nodo == destino:
            break

        for vecino, peso in grafo[nodo].items():
            nueva_dist = dist[nodo] + peso
            if nueva_dist < dist[vecino]:
                dist[vecino]   = nueva_dist
                previo[vecino] = nodo
                heapq.heappush(heap, (nueva_dist, vecino))

    if dist[destino] == float("inf"):
        return None, None

    camino = reconstruir_camino(previo, origen, destino)
    return dist[destino], camino
