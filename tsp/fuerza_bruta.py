"""
fuerza_bruta.py

Algoritmo de Fuerza Bruta para el Problema del Viajero (TSP).

Idea principal:
Prueba todas las rutas posibles entre las provincias seleccionadas
y escoge la ruta con menor distancia total.

Ventaja:
- Encuentra la solución óptima.

Desventaja:
- Es muy lento cuando aumenta el número de provincias.
- Se recomienda usarlo solo con pocas provincias.
"""

from itertools import permutations

from tsp.tsp_utils import (
    calcular_distancia_total_matriz,
    construir_matriz_distancias,
)


def fuerza_bruta_tsp(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
    max_provincias: int = 9,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando Fuerza Bruta.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: coordenadas de las provincias.
    - provincia_inicio: provincia inicial de la ruta.
    - volver_inicio: si es True, vuelve a la provincia inicial.
    - max_provincias: límite máximo para evitar tiempos muy largos.

    Retorna:
    - mejor_distancia: distancia mínima encontrada.
    - mejor_ruta: ruta con menor distancia.
    """

    if not provincias or len(provincias) < 2:
        return None, None

    # Eliminar duplicados sin perder el orden
    provincias = list(dict.fromkeys(provincias))

    # Seguridad: fuerza bruta crece demasiado rápido
    if len(provincias) > max_provincias:
        return None, None

    # Si no se indica inicio, se toma la primera provincia
    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    # Si el inicio no está en la lista, se agrega
    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    # Provincias que se permutarán, sin incluir la inicial
    restantes = [
        provincia
        for provincia in provincias
        if provincia != provincia_inicio
    ]

    matriz = construir_matriz_distancias(provincias, coords)

    mejor_distancia = float("inf")
    mejor_ruta = None

    # Probar todas las combinaciones posibles
    for permutacion in permutations(restantes):
        ruta = [provincia_inicio] + list(permutacion)

        if volver_inicio:
            ruta_completa = ruta + [provincia_inicio]
        else:
            ruta_completa = ruta

        distancia = calcular_distancia_total_matriz(
            ruta_completa,
            matriz,
            volver_inicio=False,
        )

        if distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_ruta = ruta_completa

    return mejor_distancia, mejor_ruta