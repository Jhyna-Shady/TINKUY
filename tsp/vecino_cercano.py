"""
vecino_cercano.py

Algoritmo del Vecino más Cercano para el Problema del Viajero (TSP).

Idea principal:
Desde una provincia inicial, el algoritmo siempre elige como siguiente destino
la provincia no visitada más cercana.

Este algoritmo es heurístico, es decir, busca una buena solución rápidamente,
pero no siempre garantiza la ruta óptima.
"""

from tsp.tsp_utils import (
    calcular_distancia_total_matriz,
    construir_matriz_distancias,
)


def vecino_mas_cercano(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando el algoritmo del Vecino más Cercano.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: diccionario con coordenadas de las provincias.
    - provincia_inicio: provincia desde donde inicia la ruta.
    - volver_inicio: si es True, la ruta termina regresando al punto inicial.

    Retorna:
    - distancia_total: distancia total de la ruta en kilómetros.
    - ruta: lista ordenada de provincias visitadas.
    """

    # Validar cantidad mínima de provincias
    if not provincias or len(provincias) < 2:
        return None, None

    # Eliminar duplicados sin perder el orden
    provincias = list(dict.fromkeys(provincias))

    # Si no se indica provincia inicial, se toma la primera
    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    # Si la provincia inicial no está en la lista, se agrega al inicio
    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    # Construir matriz de distancias para evitar recalcular muchas veces
    matriz = construir_matriz_distancias(provincias, coords)

    # Inicializar ruta
    actual = provincia_inicio
    ruta = [actual]

    # Provincias pendientes de visitar
    no_visitadas = set(provincias)
    no_visitadas.remove(actual)

    # Mientras existan provincias sin visitar
    while no_visitadas:
        siguiente = min(
            no_visitadas,
            key=lambda provincia: matriz[actual][provincia],
        )

        ruta.append(siguiente)
        no_visitadas.remove(siguiente)
        actual = siguiente

    # Si se desea volver al inicio, se agrega la provincia inicial al final
    if volver_inicio:
        ruta.append(provincia_inicio)

    # Calcular distancia total de la ruta obtenida
    distancia_total = calcular_distancia_total_matriz(
        ruta,
        matriz,
        volver_inicio=False,
    )

    return distancia_total, ruta