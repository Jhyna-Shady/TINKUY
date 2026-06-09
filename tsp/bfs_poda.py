"""
bfs_poda.py

Algoritmo BFS con poda para el Problema del Viajero (TSP).

Idea principal:
Explora rutas por niveles usando una cola.
Cada estado representa una ruta parcial.

BFS = Breadth First Search = búsqueda en amplitud.
Poda = descartar rutas parciales que ya son peores que la mejor solución encontrada.
"""

from collections import deque

from tsp.tsp_utils import construir_matriz_distancias


def bfs_poda_tsp(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
    max_provincias: int = 10,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando BFS con poda.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: coordenadas de las provincias.
    - provincia_inicio: provincia inicial.
    - volver_inicio: si es True, vuelve a la provincia inicial.
    - max_provincias: límite de seguridad para evitar que el algoritmo sea muy lento.

    Retorna:
    - mejor_distancia
    - mejor_ruta
    """

    if not provincias or len(provincias) < 2:
        return None, None

    # Eliminar duplicados sin perder el orden
    provincias = list(dict.fromkeys(provincias))

    # Seguridad: BFS también puede crecer mucho
    if len(provincias) > max_provincias:
        return None, None

    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    matriz = construir_matriz_distancias(provincias, coords)

    mejor_distancia = float("inf")
    mejor_ruta = None

    # Cola de estados:
    # cada estado contiene:
    # provincia actual, visitadas, ruta actual, distancia acumulada
    cola = deque()
    cola.append(
        (
            provincia_inicio,
            {provincia_inicio},
            [provincia_inicio],
            0.0,
        )
    )

    while cola:
        actual, visitadas, ruta_actual, distancia_actual = cola.popleft()

        # Poda: si esta ruta ya es peor que la mejor, no sigue
        if distancia_actual >= mejor_distancia:
            continue

        # Caso base: ya visitó todas las provincias
        if len(visitadas) == len(provincias):
            ruta_final = ruta_actual.copy()
            distancia_final = distancia_actual

            if volver_inicio:
                distancia_final += matriz[actual][provincia_inicio]
                ruta_final.append(provincia_inicio)

            if distancia_final < mejor_distancia:
                mejor_distancia = distancia_final
                mejor_ruta = ruta_final

            continue

        # Provincias pendientes
        pendientes = [
            provincia
            for provincia in provincias
            if provincia not in visitadas
        ]

        # Ordenamos por cercanía para encontrar buenas rutas antes
        pendientes.sort(key=lambda provincia: matriz[actual][provincia])

        for siguiente in pendientes:
            nueva_distancia = distancia_actual + matriz[actual][siguiente]

            # Segunda poda antes de agregar a la cola
            if nueva_distancia >= mejor_distancia:
                continue

            cola.append(
                (
                    siguiente,
                    visitadas | {siguiente},
                    ruta_actual + [siguiente],
                    nueva_distancia,
                )
            )

    if mejor_ruta is None:
        return None, None

    return mejor_distancia, mejor_ruta