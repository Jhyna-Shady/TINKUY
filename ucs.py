# ucs.py
# Uniform Cost Search (UCS) — Dijkstra expresado como búsqueda en árbol
#
# Complejidad: O((V + E) log V), equivalente a Dijkstra.
# Diferencia conceptual: UCS expande el nodo de MENOR COSTE ACUMULADO
# sin mantener un array global de distancias; en cambio, marca nodos
# como "cerrados" al extraerlos del heap (paradigma de búsqueda en árbol).
# En grafos con ciclos produce el mismo resultado que Dijkstra.

import heapq
from utils import reconstruir_camino


def ucs(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,  # ignorado; firma uniforme
) -> tuple[float | None, list[str] | None]:
    """
    Encuentra la ruta de menor coste entre `origen` y `destino` usando UCS.

    Parámetros
    ----------
    grafo   : {nodo: {vecino: peso_km}}
    origen  : nodo de partida
    destino : nodo de llegada
    coords  : no utilizado

    Retorna
    -------
    (distancia_total_km, lista_de_nodos) o (None, None) si no hay ruta.
    """
    if origen not in grafo or destino not in grafo:
        return None, None

    # heap: (coste_acumulado, nodo)
    heap   = [(0.0, origen)]
    previo = {origen: None}
    cerrado: set[str] = set()       # nodos ya expandidos

    coste: dict[str, float] = {origen: 0.0}

    while heap:
        g, nodo = heapq.heappop(heap)

        # Nodo ya expandido → descartamos entrada obsoleta del heap
        if nodo in cerrado:
            continue
        cerrado.add(nodo)

        # Goal test al expandir (no al insertar) → garantiza optimalidad
        if nodo == destino:
            camino = reconstruir_camino(previo, origen, destino)
            return g, camino

        for vecino, peso in grafo[nodo].items():
            if vecino in cerrado:
                continue
            nuevo_coste = g + peso
            if vecino not in coste or nuevo_coste < coste[vecino]:
                coste[vecino]  = nuevo_coste
                previo[vecino] = nodo
                heapq.heappush(heap, (nuevo_coste, vecino))

    return None, None
