# greedy_bfs.py
# Greedy Best-First Search — expansión guiada solo por la heurística
#
# Complejidad: O(E log V) en promedio, aunque puede ser subóptimo.
# Diferencia clave frente a A*: el heap se ordena SOLO por h(n),
# ignorando el coste acumulado g(n). Más rápido, pero no garantiza
# la ruta óptima.

import heapq
from utils import haversine, reconstruir_camino


def greedy_bfs(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,
) -> tuple[float | None, list[str] | None]:
    """
    Encuentra una ruta (no necesariamente óptima) entre `origen` y `destino`
    expandiendo siempre el nodo más prometedor según Haversine.

    Parámetros
    ----------
    grafo   : {nodo: {vecino: peso_km}}
    origen  : nodo de partida
    destino : nodo de llegada
    coords  : {nodo: (lat, lon)} — requerido para la heurística

    Retorna
    -------
    (distancia_total_km, lista_de_nodos) o (None, None) si no hay ruta.
    La distancia retornada es el coste real del camino encontrado,
    NO la estimación heurística.
    """
    if origen not in grafo or destino not in grafo:
        return None, None

    if coords is None:
        coords = {}

    def h(nodo: str) -> float:
        if nodo in coords and destino in coords:
            return haversine(coords[nodo], coords[destino])
        return 0.0

    # g_real[n] = coste real acumulado desde origen (para reportar distancia)
    g_real  = {origen: 0.0}
    previo  = {origen: None}
    visitado: set[str] = set()

    # heap: (h(nodo), nodo)
    heap = [(h(origen), origen)]

    while heap:
        _, nodo = heapq.heappop(heap)

        if nodo in visitado:
            continue
        visitado.add(nodo)

        if nodo == destino:
            camino = reconstruir_camino(previo, origen, destino)
            return g_real.get(destino), camino

        for vecino, peso in grafo[nodo].items():
            if vecino not in visitado:
                coste_candidato = g_real[nodo] + peso
                # Actualizar solo si encontramos un camino más corto al vecino
                if vecino not in g_real or coste_candidato < g_real[vecino]:
                    g_real[vecino] = coste_candidato
                    previo[vecino] = nodo
                heapq.heappush(heap, (h(vecino), vecino))

    return None, None
