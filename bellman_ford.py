# bellman_ford.py
# Algoritmo de Bellman-Ford — ruta mínima con soporte para pesos negativos
#
# Complejidad: O(V · E)
# Ventaja frente a Dijkstra: tolera aristas de peso negativo y detecta
# ciclos negativos (poco relevante en grafos de distancias, pero correcto).

from utils import reconstruir_camino


def bellman_ford(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,  # ignorado; firma uniforme
) -> tuple[float | None, list[str] | None]:
    """
    Encuentra la ruta de menor distancia entre `origen` y `destino`.

    Parámetros
    ----------
    grafo   : {nodo: {vecino: peso_km}}
    origen  : nodo de partida
    destino : nodo de llegada
    coords  : no utilizado

    Retorna
    -------
    (distancia_total_km, lista_de_nodos) o (None, None) si no hay ruta
    o se detecta un ciclo negativo.
    """
    if origen not in grafo or destino not in grafo:
        return None, None

    nodos  = list(grafo.keys())
    V      = len(nodos)

    dist   = {nodo: float("inf") for nodo in nodos}
    previo = {nodo: None         for nodo in nodos}
    dist[origen] = 0.0

    # Construir lista de aristas (u, v, peso)
    aristas: list[tuple[str, str, float]] = []
    for u, vecinos in grafo.items():
        for v, peso in vecinos.items():
            aristas.append((u, v, peso))

    # Relajar V-1 veces
    for _ in range(V - 1):
        actualizado = False
        for u, v, peso in aristas:
            if dist[u] != float("inf") and dist[u] + peso < dist[v]:
                dist[v]   = dist[u] + peso
                previo[v] = u
                actualizado = True
        if not actualizado:
            break  # convergencia temprana

    # Detección de ciclo negativo (V-ésima pasada)
    for u, v, peso in aristas:
        if dist[u] != float("inf") and dist[u] + peso < dist[v]:
            # Ciclo negativo detectado — resultado no confiable
            return None, None

    if dist[destino] == float("inf"):
        return None, None

    camino = reconstruir_camino(previo, origen, destino)
    return dist[destino], camino
