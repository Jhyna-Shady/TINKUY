"""
two_opt.py

Algoritmo 2-opt para el Problema del Viajero (TSP).

Idea principal:
Parte de una ruta inicial y mejora la solución intercambiando segmentos.

Ejemplo:
Ruta inicial:
A → B → C → D → E

2-opt puede invertir un tramo:
A → D → C → B → E

Si la nueva ruta es más corta, se conserva.
"""

from tsp.tsp_utils import (
    calcular_distancia_total_matriz,
    construir_matriz_distancias,
)
from tsp.vecino_cercano import vecino_mas_cercano


def _aplicar_intercambio_2opt(
    ruta: list[str],
    i: int,
    k: int,
) -> list[str]:
    """
    Invierte el segmento de la ruta entre las posiciones i y k.

    Ejemplo:
    ruta = [A, B, C, D, E]
    i = 1, k = 3

    resultado:
    [A, D, C, B, E]
    """

    return ruta[:i] + ruta[i:k + 1][::-1] + ruta[k + 1:]


def two_opt_tsp(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
    max_iteraciones: int = 100,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando 2-opt.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: coordenadas de las provincias.
    - provincia_inicio: provincia inicial.
    - volver_inicio: si es True, la ruta vuelve al inicio.
    - max_iteraciones: límite de mejoras para evitar ciclos muy largos.

    Retorna:
    - mejor_distancia
    - mejor_ruta
    """

    if not provincias or len(provincias) < 2:
        return None, None

    # Eliminar duplicados sin perder el orden
    provincias = list(dict.fromkeys(provincias))

    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    # Primero generamos una ruta inicial usando vecino más cercano
    distancia_inicial, ruta_inicial = vecino_mas_cercano(
        provincias=provincias,
        coords=coords,
        provincia_inicio=provincia_inicio,
        volver_inicio=volver_inicio,
    )

    if ruta_inicial is None:
        return None, None

    # Si vuelve al inicio, temporalmente quitamos la última provincia repetida
    if volver_inicio and ruta_inicial[0] == ruta_inicial[-1]:
        ruta_actual = ruta_inicial[:-1]
    else:
        ruta_actual = ruta_inicial.copy()

    matriz = construir_matriz_distancias(provincias, coords)

    mejor_ruta = ruta_actual
    mejor_distancia = calcular_distancia_total_matriz(
        mejor_ruta,
        matriz,
        volver_inicio=volver_inicio,
    )

    mejora = True
    iteracion = 0

    while mejora and iteracion < max_iteraciones:
        mejora = False
        iteracion += 1

        # No tocamos la posición 0 para mantener fija la provincia inicial
        for i in range(1, len(mejor_ruta) - 1):
            for k in range(i + 1, len(mejor_ruta)):
                nueva_ruta = _aplicar_intercambio_2opt(
                    mejor_ruta,
                    i,
                    k,
                )

                nueva_distancia = calcular_distancia_total_matriz(
                    nueva_ruta,
                    matriz,
                    volver_inicio=volver_inicio,
                )

                if nueva_distancia < mejor_distancia:
                    mejor_ruta = nueva_ruta
                    mejor_distancia = nueva_distancia
                    mejora = True
                    break

            if mejora:
                break

    # Si se pide volver al inicio, agregamos visualmente el inicio al final
    ruta_final = mejor_ruta.copy()

    if volver_inicio:
        ruta_final.append(provincia_inicio)

    return mejor_distancia, ruta_final