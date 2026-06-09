# floyd_warshall.py
# Algoritmo de Floyd-Warshall — rutas mínimas entre TODOS los pares de nodos
#
# Complejidad: O(V³) en tiempo, O(V²) en espacio.
# Ventaja: un solo cálculo resuelve todas las consultas origen→destino.
# Desventaja: ineficiente en grafos grandes; ideal para el tamaño del grafo
# de provincias de este proyecto.
#
# Firma especial: recibe solo el grafo (sin origen/destino) porque calcula
# la matriz completa. app.py extrae el par solicitado de la matriz resultado.

from utils import reconstruir_camino


def floyd_warshall(
    grafo: dict[str, dict[str, float]],
    origen: str | None = None,        # aceptados para firma uniforme opcional
    destino: str | None = None,
    coords: dict | None = None,       # ignorado
) -> tuple[dict | None, dict | None]:
    """
    Calcula la ruta mínima entre todos los pares de nodos.

    Parámetros
    ----------
    grafo   : {nodo: {vecino: peso_km}}
    origen  : si se proporciona, retorna (distancia, camino) para ese par.
              Si es None, retorna las matrices completas.
    destino : ídem.

    Retorna
    -------
    Modo completo (origen/destino = None):
        (dist_matrix, prev_matrix)
        dist_matrix : {u: {v: distancia_km}}
        prev_matrix : {u: {v: nodo_previo}}  (para reconstruir camino)

    Modo par (origen y destino especificados):
        (distancia_km, lista_de_nodos) o (None, None)
    """
    if not grafo:
        return None, None

    nodos = list(grafo.keys())
    INF   = float("inf")

    # -----------------------------------------------------------------------
    # Inicialización de matrices
    # -----------------------------------------------------------------------
    dist = {u: {v: INF  for v in nodos} for u in nodos}
    prev = {u: {v: None for v in nodos} for u in nodos}

    for u in nodos:
        dist[u][u] = 0.0

    for u, vecinos in grafo.items():
        for v, peso in vecinos.items():
            if peso < dist[u][v]:
                dist[u][v] = peso
                prev[u][v] = u   # el predecesor de v en el camino desde u es u mismo

    # -----------------------------------------------------------------------
    # Relajación triple
    # -----------------------------------------------------------------------
    for k in nodos:
        for u in nodos:
            if dist[u][k] == INF:
                continue              # optimización: saltar filas inalcanzables
            for v in nodos:
                nueva = dist[u][k] + dist[k][v]
                if nueva < dist[u][v]:
                    dist[u][v] = nueva
                    prev[u][v] = prev[k][v]

    # -----------------------------------------------------------------------
    # Retorno según modo de uso
    # -----------------------------------------------------------------------
    if origen is not None and destino is not None:
        # Modo par: extraer un único camino
        if origen not in grafo or destino not in grafo:
            return None, None
        if dist[origen][destino] == INF:
            return None, None

        camino = _reconstruir_fw(prev, origen, destino)
        return dist[origen][destino], camino

    # Modo completo: devolver matrices
    return dist, prev


# ---------------------------------------------------------------------------
# Reconstrucción de camino para Floyd-Warshall
# (prev[u][v] = último nodo intermedio antes de v en el camino u→v)
# ---------------------------------------------------------------------------
def _reconstruir_fw(
    prev: dict[str, dict[str, str | None]],
    origen: str,
    destino: str,
) -> list[str] | None:
    """Reconstruye el camino origen→destino a partir de la matriz prev de FW."""
    if prev[origen][destino] is None and origen != destino:
        return None

    camino = [destino]
    actual = destino

    while actual != origen:
        actual = prev[origen][actual]
        if actual is None:
            return None
        camino.append(actual)

    camino.reverse()
    return camino
