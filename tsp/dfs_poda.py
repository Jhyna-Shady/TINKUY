"""
dfs_poda.py

Algoritmo DFS con poda para el Problema del Viajero (TSP).

Idea principal:
Explora rutas usando búsqueda en profundidad, pero corta una rama
cuando la distancia parcial ya supera la mejor distancia encontrada.

DFS = Depth First Search = búsqueda en profundidad.
Poda = eliminar caminos que ya no conviene explorar.
"""

from tsp.tsp_utils import construir_matriz_distancias


def dfs_poda_tsp(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
    max_provincias: int = 10,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando DFS con poda.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: coordenadas de las provincias.
    - provincia_inicio: provincia inicial.
    - volver_inicio: si es True, vuelve al punto inicial.
    - max_provincias: límite de seguridad.

    Retorna:
    - mejor_distancia
    - mejor_ruta
    """

    if not provincias or len(provincias) < 2:
        return None, None

    provincias = list(dict.fromkeys(provincias))

    if len(provincias) > max_provincias:
        return None, None

    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    matriz = construir_matriz_distancias(provincias, coords)

    mejor_distancia = float("inf")
    mejor_ruta = None

    def dfs(
        actual: str,
        visitadas: set[str],
        ruta_actual: list[str],
        distancia_actual: float,
    ) -> None:
        nonlocal mejor_distancia, mejor_ruta

        # Poda: si ya es peor que la mejor, no seguimos
        if distancia_actual >= mejor_distancia:
            return

        # Caso base: ya visitamos todas las provincias
        if len(visitadas) == len(provincias):
            ruta_final = ruta_actual.copy()
            distancia_final = distancia_actual

            if volver_inicio:
                distancia_final += matriz[actual][provincia_inicio]
                ruta_final.append(provincia_inicio)

            if distancia_final < mejor_distancia:
                mejor_distancia = distancia_final
                mejor_ruta = ruta_final

            return

        # Explorar provincias no visitadas
        for siguiente in provincias:
            if siguiente not in visitadas:
                nueva_distancia = distancia_actual + matriz[actual][siguiente]

                dfs(
                    actual=siguiente,
                    visitadas=visitadas | {siguiente},
                    ruta_actual=ruta_actual + [siguiente],
                    distancia_actual=nueva_distancia,
                )

    dfs(
        actual=provincia_inicio,
        visitadas={provincia_inicio},
        ruta_actual=[provincia_inicio],
        distancia_actual=0.0,
    )

    if mejor_ruta is None:
        return None, None

    return mejor_distancia, mejor_ruta