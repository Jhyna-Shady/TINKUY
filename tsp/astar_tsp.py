"""
astar_tsp.py

Algoritmo A* adaptado al Problema del Viajero (TSP).

Idea principal:
Explora primero las rutas que parecen más prometedoras, usando:

    prioridad = distancia_acumulada + heuristica

La heurística estima cuánto falta para completar el recorrido.
"""

import heapq
from itertools import count

from tsp.tsp_utils import construir_matriz_distancias


def _mst_costo(
    nodos: set[str],
    matriz: dict[str, dict[str, float]],
) -> float:
    """
    Calcula una aproximación del costo mínimo para conectar un conjunto de nodos.

    MST = Minimum Spanning Tree = árbol de expansión mínima.
    Es una forma de estimar cuánto falta recorrer entre provincias pendientes.
    """

    if not nodos or len(nodos) == 1:
        return 0.0

    nodos = set(nodos)
    visitados = {next(iter(nodos))}
    no_visitados = nodos - visitados

    costo_total = 0.0

    while no_visitados:
        mejor_costo = float("inf")
        mejor_nodo = None

        for nodo_visitado in visitados:
            for nodo_no_visitado in no_visitados:
                costo = matriz[nodo_visitado][nodo_no_visitado]

                if costo < mejor_costo:
                    mejor_costo = costo
                    mejor_nodo = nodo_no_visitado

        costo_total += mejor_costo
        visitados.add(mejor_nodo)
        no_visitados.remove(mejor_nodo)

    return costo_total


def _heuristica_tsp(
    actual: str,
    pendientes: set[str],
    provincia_inicio: str,
    matriz: dict[str, dict[str, float]],
    volver_inicio: bool,
) -> float:
    """
    Heurística para A* en TSP.

    Estima el costo restante usando:
    - distancia mínima desde la provincia actual hacia alguna pendiente;
    - costo aproximado para conectar las provincias pendientes;
    - si se vuelve al inicio, distancia mínima desde pendientes al inicio.
    """

    if not pendientes:
        if volver_inicio:
            return matriz[actual][provincia_inicio]
        return 0.0

    # Costo mínimo desde la provincia actual hacia una pendiente
    costo_actual_a_pendiente = min(
        matriz[actual][provincia]
        for provincia in pendientes
    )

    # Costo aproximado para conectar las provincias pendientes
    costo_mst = _mst_costo(pendientes, matriz)

    # Si debe regresar al inicio, se agrega una estimación de retorno
    costo_retorno = 0.0
    if volver_inicio:
        costo_retorno = min(
            matriz[provincia][provincia_inicio]
            for provincia in pendientes
        )

    return costo_actual_a_pendiente + costo_mst + costo_retorno


def astar_tsp(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
    max_provincias: int = 11,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando A*.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: coordenadas de las provincias.
    - provincia_inicio: provincia inicial.
    - volver_inicio: si es True, la ruta termina regresando al inicio.
    - max_provincias: límite de seguridad.

    Retorna:
    - mejor_distancia
    - mejor_ruta
    """

    if not provincias or len(provincias) < 2:
        return None, None

    # Eliminar duplicados sin perder el orden
    provincias = list(dict.fromkeys(provincias))

    # Seguridad: A* también puede crecer bastante
    if len(provincias) > max_provincias:
        return None, None

    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    matriz = construir_matriz_distancias(provincias, coords)

    todas = set(provincias)

    # Contador para evitar errores cuando dos prioridades son iguales
    contador = count()

    # Cola de prioridad:
    # prioridad, contador, distancia_acumulada, provincia_actual, visitadas, ruta
    pendientes_iniciales = todas - {provincia_inicio}

    prioridad_inicial = _heuristica_tsp(
        actual=provincia_inicio,
        pendientes=pendientes_iniciales,
        provincia_inicio=provincia_inicio,
        matriz=matriz,
        volver_inicio=volver_inicio,
    )

    cola = []
    heapq.heappush(
        cola,
        (
            prioridad_inicial,
            next(contador),
            0.0,
            provincia_inicio,
            frozenset([provincia_inicio]),
            [provincia_inicio],
        ),
    )

    # Guarda el menor costo conocido por estado
    mejor_costo_estado = {}

    while cola:
        (
            prioridad,
            _,
            distancia_actual,
            actual,
            visitadas,
            ruta_actual,
        ) = heapq.heappop(cola)

        estado = (actual, visitadas)

        if estado in mejor_costo_estado:
            if distancia_actual > mejor_costo_estado[estado]:
                continue

        mejor_costo_estado[estado] = distancia_actual

        # Si ya visitó todas las provincias, terminó
        if len(visitadas) == len(provincias):
            ruta_final = ruta_actual.copy()
            distancia_final = distancia_actual

            if volver_inicio:
                distancia_final += matriz[actual][provincia_inicio]
                ruta_final.append(provincia_inicio)

            return distancia_final, ruta_final

        no_visitadas = todas - set(visitadas)

        # Explorar siguientes provincias
        for siguiente in no_visitadas:
            nueva_distancia = distancia_actual + matriz[actual][siguiente]
            nuevas_visitadas = frozenset(set(visitadas) | {siguiente})
            nueva_ruta = ruta_actual + [siguiente]

            pendientes_restantes = todas - set(nuevas_visitadas)

            heuristica = _heuristica_tsp(
                actual=siguiente,
                pendientes=pendientes_restantes,
                provincia_inicio=provincia_inicio,
                matriz=matriz,
                volver_inicio=volver_inicio,
            )

            nueva_prioridad = nueva_distancia + heuristica

            nuevo_estado = (siguiente, nuevas_visitadas)

            if nuevo_estado in mejor_costo_estado:
                if nueva_distancia >= mejor_costo_estado[nuevo_estado]:
                    continue

            heapq.heappush(
                cola,
                (
                    nueva_prioridad,
                    next(contador),
                    nueva_distancia,
                    siguiente,
                    nuevas_visitadas,
                    nueva_ruta,
                ),
            )

    return None, None