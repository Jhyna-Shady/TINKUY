"""
algoritmo_genetico.py

Algoritmo Genético para el Problema del Viajero (TSP).

Idea principal:
Genera una población de rutas posibles y las mejora mediante:
- selección
- cruce
- mutación
- elitismo

Este algoritmo no siempre garantiza la ruta óptima, pero puede encontrar
buenas soluciones cuando hay muchas provincias.
"""

import random

from tsp.tsp_utils import (
    calcular_distancia_total_matriz,
    construir_matriz_distancias,
)


def _crear_individuo(provincias_sin_inicio: list[str]) -> list[str]:
    """
    Crea una ruta aleatoria sin incluir la provincia inicial.

    Ejemplo:
    ["ICA", "AREQUIPA", "CUSCO", "PUNO"]
    """

    individuo = provincias_sin_inicio.copy()
    random.shuffle(individuo)
    return individuo


def _crear_poblacion(
    provincias_sin_inicio: list[str],
    tamano_poblacion: int,
) -> list[list[str]]:
    """
    Crea la población inicial de rutas aleatorias.
    """

    return [
        _crear_individuo(provincias_sin_inicio)
        for _ in range(tamano_poblacion)
    ]


def _distancia_individuo(
    individuo: list[str],
    provincia_inicio: str,
    matriz: dict[str, dict[str, float]],
    volver_inicio: bool,
) -> float:
    """
    Calcula la distancia total de un individuo.

    El individuo no contiene la provincia inicial, por eso se agrega al inicio.
    """

    ruta = [provincia_inicio] + individuo

    return calcular_distancia_total_matriz(
        ruta,
        matriz,
        volver_inicio=volver_inicio,
    )


def _seleccion_torneo(
    poblacion: list[list[str]],
    provincia_inicio: str,
    matriz: dict[str, dict[str, float]],
    volver_inicio: bool,
    tamano_torneo: int = 3,
) -> list[str]:
    """
    Selecciona un individuo usando torneo.

    Torneo = se eligen varios candidatos al azar y gana el de menor distancia.
    """

    candidatos = random.sample(
        poblacion,
        k=min(tamano_torneo, len(poblacion)),
    )

    ganador = min(
        candidatos,
        key=lambda individuo: _distancia_individuo(
            individuo,
            provincia_inicio,
            matriz,
            volver_inicio,
        ),
    )

    return ganador.copy()


def _cruce_ordenado(
    padre1: list[str],
    padre2: list[str],
) -> list[str]:
    """
    Cruce ordenado OX.

    Toma un segmento del padre 1 y completa el resto con el orden del padre 2.

    Ejemplo:
    padre1 = [A, B, C, D, E]
    padre2 = [C, A, E, B, D]

    El hijo mantiene un segmento de padre1 y completa sin repetir provincias.
    """

    n = len(padre1)

    if n <= 2:
        return padre1.copy()

    inicio, fin = sorted(random.sample(range(n), 2))

    hijo = [None] * n

    # Copiar segmento del padre 1
    hijo[inicio:fin + 1] = padre1[inicio:fin + 1]

    # Completar con genes del padre 2 sin repetir
    posicion = 0

    for gen in padre2:
        if gen not in hijo:
            while hijo[posicion] is not None:
                posicion += 1
            hijo[posicion] = gen

    return hijo


def _mutacion_intercambio(
    individuo: list[str],
    tasa_mutacion: float,
) -> list[str]:
    """
    Aplica mutación por intercambio.

    Mutación = cambia dos provincias de posición para generar variedad.
    """

    nuevo = individuo.copy()

    if len(nuevo) < 2:
        return nuevo

    if random.random() < tasa_mutacion:
        i, j = random.sample(range(len(nuevo)), 2)
        nuevo[i], nuevo[j] = nuevo[j], nuevo[i]

    return nuevo


def algoritmo_genetico_tsp(
    provincias: list[str],
    coords: dict[str, tuple[float, float]],
    provincia_inicio: str | None = None,
    volver_inicio: bool = False,
    tamano_poblacion: int = 80,
    generaciones: int = 300,
    tasa_mutacion: float = 0.15,
    elite: int = 2,
    semilla: int | None = 42,
) -> tuple[float | None, list[str] | None]:
    """
    Resuelve el TSP usando Algoritmo Genético.

    Parámetros:
    - provincias: lista de provincias seleccionadas.
    - coords: coordenadas de las provincias.
    - provincia_inicio: provincia inicial.
    - volver_inicio: si es True, vuelve a la provincia inicial.
    - tamano_poblacion: cantidad de rutas en cada generación.
    - generaciones: número de ciclos evolutivos.
    - tasa_mutacion: probabilidad de cambiar dos provincias de posición.
    - elite: cantidad de mejores individuos que pasan directo a la siguiente generación.
    - semilla: valor para que los resultados sean reproducibles.

    Retorna:
    - mejor_distancia
    - mejor_ruta
    """

    if semilla is not None:
        random.seed(semilla)

    if not provincias or len(provincias) < 2:
        return None, None

    # Eliminar duplicados sin perder el orden
    provincias = list(dict.fromkeys(provincias))

    if provincia_inicio is None:
        provincia_inicio = provincias[0]

    if provincia_inicio not in provincias:
        provincias.insert(0, provincia_inicio)

    # Provincias que se ordenarán genéticamente, sin mover el inicio
    provincias_sin_inicio = [
        provincia
        for provincia in provincias
        if provincia != provincia_inicio
    ]

    if not provincias_sin_inicio:
        return None, None

    matriz = construir_matriz_distancias(provincias, coords)

    # Crear población inicial
    poblacion = _crear_poblacion(
        provincias_sin_inicio,
        tamano_poblacion,
    )

    mejor_individuo = None
    mejor_distancia = float("inf")

    for _ in range(generaciones):

        # Ordenar población por distancia
        poblacion.sort(
            key=lambda individuo: _distancia_individuo(
                individuo,
                provincia_inicio,
                matriz,
                volver_inicio,
            )
        )

        # Actualizar mejor individuo global
        distancia_actual = _distancia_individuo(
            poblacion[0],
            provincia_inicio,
            matriz,
            volver_inicio,
        )

        if distancia_actual < mejor_distancia:
            mejor_distancia = distancia_actual
            mejor_individuo = poblacion[0].copy()

        # Nueva generación con elitismo
        nueva_poblacion = [
            individuo.copy()
            for individuo in poblacion[:elite]
        ]

        # Completar nueva población
        while len(nueva_poblacion) < tamano_poblacion:
            padre1 = _seleccion_torneo(
                poblacion,
                provincia_inicio,
                matriz,
                volver_inicio,
            )

            padre2 = _seleccion_torneo(
                poblacion,
                provincia_inicio,
                matriz,
                volver_inicio,
            )

            hijo = _cruce_ordenado(padre1, padre2)

            hijo = _mutacion_intercambio(
                hijo,
                tasa_mutacion,
            )

            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    if mejor_individuo is None:
        return None, None

    mejor_ruta = [provincia_inicio] + mejor_individuo

    if volver_inicio:
        mejor_ruta.append(provincia_inicio)

    return mejor_distancia, mejor_ruta