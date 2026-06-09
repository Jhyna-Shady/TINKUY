# 🗺️ TINKUY — Rutas y Viajero entre Provincias del Perú

Aplicación interactiva desarrollada en **Python + Streamlit** que implementa y compara algoritmos de **camino mínimo** y del **Problema del Viajero (TSP)** sobre un grafo geoespacial real construido a partir de los datos oficiales de las 196 provincias del Perú.

> **Proyecto TINKUY** — Inteligencia Artificial aplicada a grafos geoespaciales del Perú.

**Autores:**
- Ccama Itusaca Jhyna Shady
- Quispe Tapia Alex Daniel

---

## 🚀 Instalación y Ejecución

### Requisitos

- Python 3.10 o superior
- Las siguientes librerías:

```
streamlit
pydeck
pandas
geopandas
shapely
```

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/Jhyna-Shady/TINKUY
cd TINKUY

# 2. Instalar dependencias
pip install streamlit pydeck pandas geopandas shapely

# 3. Generar el grafo desde el GeoJSON (solo la primera vez)
python generar_grafo.py

# 4. Lanzar la aplicación
streamlit run app.py
```

La aplicación abre automáticamente en `http://localhost:8501`.

> ⚠️ El paso 3 debe ejecutarse **antes** de iniciar la app. Genera el archivo `grafo_completo.json` que contiene el grafo completo de provincias. Si no existe, la aplicación mostrará un error al arrancar.

---

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Obtención de Datos](#obtención-de-datos)
- [Algoritmos de Camino Mínimo](#algoritmos-de-camino-mínimo)
- [Algoritmos TSP](#algoritmos-tsp)
- [Interfaz de la Aplicación](#interfaz-de-la-aplicación)
- [Comparativa de Algoritmos](#comparativa-de-algoritmos)

---

## Visión General

El proyecto aborda dos problemas clásicos de teoría de grafos sobre el territorio peruano:

**Camino mínimo:** dado un origen y un destino, encontrar la ruta más corta entre dos provincias. El grafo modela cada provincia como un nodo con su centroide geográfico real, y cada colindancia como una arista con peso igual a la distancia Haversine en km.

**Problema del Viajero (TSP):** dado un conjunto de provincias, encontrar el recorrido más corto que las visite todas exactamente una vez y regrese al punto de partida. Se implementan tanto enfoques exactos como heurísticos y metaheurísticos.

---

## Estructura del Proyecto

```
TINKUY/
│
├── peru_provincial_simple.geojson   ← Fuente de datos (IGN, 196 provincias)
├── generar_grafo.py                 ← Preprocesamiento: GeoJSON → JSON
├── grafo_completo.json              ← Grafo generado (196 nodos, ~800 conexiones)
│
├── data.py                          ← Carga el JSON y expone la API de datos
├── utils.py                         ← Haversine + reconstrucción de caminos
│
│   ── Camino mínimo ──
├── algorithms.py                    ← Punto de entrada unificado
├── dijkstra.py
├── a_star.py
├── bellman_ford.py
├── bidireccional.py
├── greedy_bfs.py
├── floyd_warshall.py
├── ucs.py
│
│   ── TSP ──
└── tsp/
    ├── fuerza_bruta.py
    ├── dfs_poda.py
    ├── bfs_poda.py
    ├── astar_tsp.py
    ├── vecino_cercano.py
    ├── two_opt.py
    ├── algoritmo_genetico.py
    └── tsp_utils.py
│
└── app.py                           ← Interfaz Streamlit (ambos módulos)
```

---

## Obtención de Datos

La fuente de datos es el archivo `peru_provincial_simple.geojson` con los polígonos oficiales de las 196 provincias del Perú en WGS-84 (EPSG:4326), provisto por el IGN.

El script `generar_grafo.py` lo transforma en el grafo de trabajo siguiendo 5 pasos:

1. **Carga y normalización** — Lee el GeoJSON con `geopandas` y normaliza los nombres de provincias.
2. **Centroides** — Reproyecta los polígonos a UTM Zona 18S (EPSG:32718) para calcular centroides geométricamente correctos, y los convierte de vuelta a WGS-84.
3. **Colindancias** — Aplica un buffer de 50 metros a cada polígono y detecta vecinos con `sjoin(predicate="intersects")`. El buffer tolera las pequeñas brechas que introduce la simplificación geométrica del GeoJSON.
4. **Distancias** — Calcula la distancia Haversine entre los centroides de cada par colindante.
5. **Exportación** — Guarda todo en `grafo_completo.json`, con los adyacentes de cada provincia ordenados por distancia.

---

## Algoritmos de Camino Mínimo

Dado un origen y un destino, estos algoritmos encuentran la ruta de menor distancia total. Todos devuelven la distancia en km y la lista ordenada de provincias del camino, o `None` si no hay ruta.

### Dijkstra
Expande siempre el nodo de menor distancia acumulada usando un min-heap. Garantiza la ruta óptima para grafos con pesos no negativos. Es el algoritmo de referencia del proyecto. **Complejidad:** O((V+E) log V).

### A\* (A-estrella)
Extiende Dijkstra añadiendo una heurística que estima el coste restante al destino usando Haversine. Al ordenar por `f = g + h` (coste real + estimación), se dirige hacia el destino explorando menos nodos que Dijkstra sin sacrificar optimalidad. **Complejidad:** O(E log V) promedio.

### Bellman-Ford
Relaja todas las aristas del grafo V−1 veces. Más lento que Dijkstra pero capaz de manejar pesos negativos y detectar ciclos negativos. Incluye convergencia temprana. **Complejidad:** O(V·E).

### Dijkstra Bidireccional
Lanza dos búsquedas simultáneas: una desde el origen y otra desde el destino sobre el grafo inverso. Se detiene cuando la suma de los mínimos de ambas fronteras supera la mejor distancia conocida. Más eficiente en grafos grandes. **Complejidad:** ~½ Dijkstra en la práctica.

### Greedy Best-First Search
Ordena el heap únicamente por la heurística Haversine, ignorando el coste acumulado. Es el más rápido pero no garantiza la ruta óptima: prioriza lo que parece más cerca al destino en línea recta, sin considerar el camino ya recorrido. **Complejidad:** O(E log V) promedio.

### Floyd-Warshall
Calcula la ruta mínima entre **todos los pares** de nodos en una sola ejecución mediante programación dinámica. El coste O(V³) se amortiza cuando se necesitan múltiples consultas sobre el mismo grafo. **Complejidad:** O(V³) tiempo, O(V²) espacio.

### UCS (Uniform Cost Search)
Reformulación de Dijkstra bajo el paradigma de búsqueda en árbol: aplica el test de llegada al expandir (no al insertar) y mantiene un conjunto explícito de nodos cerrados. Produce resultados idénticos a Dijkstra. **Complejidad:** O((V+E) log V).

---

## Algoritmos TSP

El Problema del Viajero (TSP) busca el recorrido más corto que visita un conjunto de provincias exactamente una vez y regresa al origen. El módulo `tsp/` contiene tanto enfoques exactos como heurísticos y metaheurísticos.

### Fuerza Bruta (`fuerza_bruta.py`)
Evalúa todas las permutaciones posibles del conjunto de nodos y selecciona la de menor coste total. Garantiza la solución óptima pero es inviable para más de ~12 nodos por su crecimiento factorial. **Complejidad:** O(n!).

### DFS con Poda (`dfs_poda.py`)
Búsqueda en profundidad con poda de ramas cuyo coste parcial ya supera la mejor solución encontrada. Reduce el espacio de búsqueda respecto a fuerza bruta, pero sigue siendo exponencial en el peor caso. **Complejidad:** O(n!) reducido por poda.

### BFS con Poda (`bfs_poda.py`)
Búsqueda en anchura con poda por coste. Explora el árbol de soluciones nivel a nivel descartando ramas no prometedoras. Útil para encontrar la solución óptima en instancias pequeñas con garantía de exploración completa por nivel. **Complejidad:** O(n!) reducido por poda.

### A\* para TSP (`astar_tsp.py`)
Adapta el algoritmo A\* al espacio de estados del TSP. El estado es el conjunto de nodos visitados y el nodo actual; la heurística estima el coste mínimo restante para completar el tour. Más eficiente que BFS/DFS en instancias medianas. **Complejidad:** exponencial, mejor en práctica con buena heurística.

### Vecino Más Cercano (`vecino_cercano.py`)
Heurística constructiva greedy: desde el nodo inicial, siempre se desplaza al nodo no visitado más cercano hasta completar el tour. Muy rápido y produce soluciones razonables, aunque no garantiza el óptimo. **Complejidad:** O(n²).

### 2-Opt (`two_opt.py`)
Heurística de mejora local: toma un tour inicial e iterativamente intercambia pares de aristas si el resultado reduce la distancia total. Se repite hasta que no haya mejora posible. Suele producir soluciones cercanas al óptimo a partir de cualquier tour inicial. **Complejidad:** O(n²) por iteración.

### Algoritmo Genético (`algoritmo_genetico.py`)
Metaheurística evolutiva que mantiene una población de tours candidatos. En cada generación aplica selección, cruce (crossover) y mutación para evolucionar hacia soluciones de menor coste. Escala bien a instancias grandes donde los métodos exactos son inviables. **Complejidad:** O(generaciones × población × n).

---

## Interfaz de la Aplicación

La interfaz usa `layout="wide"` con un sidebar de controles y un área principal organizada en pestañas, cubriendo ambos módulos del proyecto.

**Sidebar:** selección del modo (camino mínimo o TSP), selectores de provincias, elección de algoritmos y botón de ejecución.

**🗺️ Mapa Interactivo:** Mapa Pydeck con polígonos provinciales como fondo (GeoJsonLayer), los 196 nodos, y la ruta resultante dibujada sobre el mapa con nodos diferenciados por color. Para TSP muestra el tour completo cerrado.

**📊 Tabla Comparativa:** Resultados de cada algoritmo con distancia, pasos y tiempo de ejecución. Código de color para identificar la solución óptima o más cercana al óptimo.

**⏱️ Rendimiento:** Gráficos de barras de tiempos y distancias, y análisis de suboptimalidad respecto a la mejor solución encontrada.

---

## Comparativa de Algoritmos

### Camino Mínimo

| Algoritmo | Óptimo | Heurística | Complejidad | Cuándo usarlo |
|---|---|---|---|---|
| Dijkstra | ✅ | No | O((V+E) log V) | Caso general, referencia |
| A\* | ✅ | ✅ Haversine | O(E log V) prom. | Grafos geográficos, más rápido |
| Bellman-Ford | ✅ | No | O(V·E) | Si hubiera pesos negativos |
| Bidireccional | ✅ | No | ~½ Dijkstra | Grafos grandes y simétricos |
| Greedy BFS | ⚠️ | ✅ Haversine | O(E log V) prom. | Aproximación rápida |
| Floyd-Warshall | ✅ | No | O(V³) | Múltiples consultas al mismo grafo |
| UCS | ✅ | No | O((V+E) log V) | Paradigma de búsqueda en árbol (IA) |

### TSP

| Algoritmo | Óptimo | Tipo | Complejidad | Cuándo usarlo |
|---|---|---|---|---|
| Fuerza Bruta | ✅ | Exacto | O(n!) | Hasta ~12 nodos |
| DFS con Poda | ✅ | Exacto | O(n!) podado | Instancias pequeñas |
| BFS con Poda | ✅ | Exacto | O(n!) podado | Instancias pequeñas |
| A\* TSP | ✅ | Exacto | Exponencial | Instancias medianas |
| Vecino Cercano | ⚠️ | Heurístico | O(n²) | Solución inicial rápida |
| 2-Opt | ⚠️ | Mejora local | O(n²)/iter | Refinamiento de tours |
| Genético | ⚠️ | Metaheurístico | O(gen·pob·n) | Instancias grandes |

---

## Repositorio

🔗 [https://github.com/Jhyna-Shady/TINKUY](https://github.com/Jhyna-Shady/TINKUY)
