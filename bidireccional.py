# bidireccional.py
# Dijkstra Bidireccional — expansión simultánea desde origen y destino
#
# Complejidad: O((V + E) log V) pero con constante ~2x menor que Dijkstra
# unidireccional en grafos grandes, porque cada frontera recorre ~√E aristas.
#
# Criterio de parada: cuando un nodo es extraído del heap de AMBAS fronteras,
# el mejor camino pasante ya fue encontrado (variante de Pohl, 1971).

import heapq
from utils import reconstruir_camino


def bidireccional(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,  # ignorado; firma uniforme
) -> tuple[float | None, list[str] | None]:
    """
    Dijkstra bidireccional entre `origen` y `destino`.

    Retorna
    -------
    (distancia_total_km, lista_de_nodos) o (None, None) si no hay ruta.
    """
    if origen not in grafo or destino not in grafo:
        return None, None

    if origen == destino:
        return 0.0, [origen]

    # -----------------------------------------------------------------------
    # Construir grafo inverso (para la búsqueda hacia atrás)
    # -----------------------------------------------------------------------
    grafo_inv: dict[str, dict[str, float]] = {n: {} for n in grafo}
    for u, vecinos in grafo.items():
        for v, peso in vecinos.items():
            grafo_inv[v][u] = peso

    INF = float("inf")

    # Distancias y predecesores para frontera delantera (F) y trasera (B)
    dist_f  = {n: INF  for n in grafo}; dist_f[origen]  = 0.0
    dist_b  = {n: INF  for n in grafo}; dist_b[destino] = 0.0
    prev_f  = {n: None for n in grafo}
    prev_b  = {n: None for n in grafo}

    heap_f = [(0.0, origen)]
    heap_b = [(0.0, destino)]

    visitado_f: set[str] = set()
    visitado_b: set[str] = set()

    mejor_dist = INF
    nodo_medio = None

    def _actualizar_mejor(nodo: str) -> None:
        nonlocal mejor_dist, nodo_medio
        candidato = dist_f[nodo] + dist_b[nodo]
        if candidato < mejor_dist:
            mejor_dist = candidato
            nodo_medio = nodo

    while heap_f or heap_b:
        # --- Paso frontera delantera ---
        if heap_f:
            d, u = heapq.heappop(heap_f)
            if d <= dist_f[u]:
                visitado_f.add(u)
                if u in visitado_b:
                    _actualizar_mejor(u)
                for v, peso in grafo[u].items():
                    nd = dist_f[u] + peso
                    if nd < dist_f[v]:
                        dist_f[v] = nd
                        prev_f[v] = u
                        heapq.heappush(heap_f, (nd, v))

        # --- Paso frontera trasera ---
        if heap_b:
            d, u = heapq.heappop(heap_b)
            if d <= dist_b[u]:
                visitado_b.add(u)
                if u in visitado_f:
                    _actualizar_mejor(u)
                for v, peso in grafo_inv[u].items():
                    nd = dist_b[u] + peso
                    if nd < dist_b[v]:
                        dist_b[v] = nd
                        prev_b[v] = u
                        heapq.heappush(heap_b, (nd, v))

        # Criterio de parada temprana: si la suma de los mínimos de ambos
        # heaps supera la mejor distancia conocida, no puede mejorar.
        min_f = heap_f[0][0] if heap_f else INF
        min_b = heap_b[0][0] if heap_b else INF
        if min_f + min_b >= mejor_dist:
            break

    if mejor_dist == INF or nodo_medio is None:
        return None, None

    # -----------------------------------------------------------------------
    # Reconstruir camino: mitad delantera + mitad trasera
    # -----------------------------------------------------------------------
    # Mitad delantera: origen → nodo_medio
    segmento_f, actual = [], nodo_medio
    while actual is not None:
        segmento_f.append(actual)
        actual = prev_f.get(actual)
    segmento_f.reverse()

    # Mitad trasera: nodo_medio → destino (siguiendo prev_b en sentido inverso)
    segmento_b, actual = [], prev_b.get(nodo_medio)
    while actual is not None:
        segmento_b.append(actual)
        actual = prev_b.get(actual)

    camino = segmento_f + segmento_b

    if not camino or camino[0] != origen or camino[-1] != destino:
        return None, None

    return mejor_dist, camino
