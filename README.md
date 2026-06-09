<<<<<<< HEAD
# TINKUY
Algoritmos de Ruta Aplicado al problema del viajero  y Camino corto usando  Provincias del Perú
=======
# 🗺️ Rutas Cortas entre Provincias del Perú

Aplicación interactiva desarrollada en **Python + Streamlit** que compara **7 algoritmos clásicos de búsqueda de camino mínimo** sobre un grafo de provincias peruanas. Permite seleccionar origen y destino, ejecutar todos los algoritmos en paralelo y comparar rutas, distancias y tiempos de ejecución en milisegundos.

---

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Estructura de Archivos](#estructura-de-archivos)
- [Datos del Grafo](#datos-del-grafo)
- [Fórmula de Haversine](#fórmula-de-haversine)
- [Algoritmos Implementados](#algoritmos-implementados)
- [Arquitectura de la Aplicación](#arquitectura-de-la-aplicación)
- [Instalación y Uso](#instalación-y-uso)
- [Comparativa de Algoritmos](#comparativa-de-algoritmos)
- [Ejemplos de Resultados](#ejemplos-de-resultados)
- [Decisiones de Diseño](#decisiones-de-diseño)

---

## Descripción del Proyecto

El proyecto resuelve el problema de **encontrar la ruta más corta** entre dos provincias del Perú modelando el territorio como un **grafo no dirigido ponderado**, donde:

- Cada **nodo** representa una provincia con coordenadas geográficas reales (latitud/longitud).
- Cada **arista** representa una conexión vial lógica con su distancia aproximada en kilómetros por carretera.
- Los **7 algoritmos** se ejecutan sobre el mismo grafo y sus resultados se comparan lado a lado.

La heurística geográfica (distancia en línea recta) se calcula mediante la **fórmula de Haversine**, lo que permite a los algoritmos informados (A\*, Greedy BFS) estimar el coste restante hasta el destino.

---

## Estructura de Archivos

```
proyecto/
│
├── app.py               # Interfaz principal de Streamlit
├── data.py              # Grafo de provincias, coordenadas y conexiones
├── utils.py             # Haversine + reconstrucción de camino (compartido)
│
├── algorithms.py        # Re-exporta todos los algoritmos (punto de entrada único)
│
├── dijkstra.py          # Algoritmo de Dijkstra
├── a_star.py            # Algoritmo A* con heurística Haversine
├── bellman_ford.py      # Algoritmo de Bellman-Ford
├── bidireccional.py     # Dijkstra Bidireccional
├── greedy_bfs.py        # Greedy Best-First Search
├── floyd_warshall.py    # Floyd-Warshall (todos los pares)
└── ucs.py               # Uniform Cost Search
```

### Responsabilidades por archivo

| Archivo | Responsabilidad |
|---|---|
| `data.py` | Fuente de verdad del grafo: coordenadas, aristas y distancias |
| `utils.py` | Lógica compartida: Haversine y reconstrucción de camino |
| `algorithms.py` | Fachada que re-exporta todos los algoritmos para `app.py` |
| `app.py` | UI Streamlit: dropdowns, visor de adyacentes, tabla comparativa, gráfico de tiempos |
| `*.py` (algoritmos) | Implementación autocontenida de cada algoritmo |

---

## Datos del Grafo

Definido en `data.py`. El grafo contiene **18 provincias** del Perú con sus coordenadas GPS reales y conexiones viales lógicas.

### Provincias incluidas

| Provincia | Latitud | Longitud | Conexiones directas |
|---|---|---|---|
| Lima | -12.0464 | -77.0428 | Ica, Huancayo, Huacho, Cerro de Pasco |
| Arequipa | -16.4090 | -71.5375 | Ica, Cusco, Puno, Moquegua, Nazca |
| Cusco | -13.5319 | -71.9675 | Arequipa, Puno, Ayacucho, Abancay, Puerto Maldonado |
| Puno | -15.8402 | -70.0219 | Cusco, Arequipa, Juliaca, Moquegua |
| Ica | -14.0678 | -75.7286 | Lima, Arequipa, Ayacucho, Nazca |
| Ayacucho | -13.1588 | -74.2236 | Ica, Cusco, Huancayo, Abancay |
| Huancayo | -12.0651 | -75.2049 | Lima, Ayacucho, Cerro de Pasco, Huánuco |
| Cerro de Pasco | -10.6860 | -76.2613 | Lima, Huancayo, Huánuco |
| Huánuco | -9.9306 | -76.2422 | Cerro de Pasco, Huancayo, Tingo María |
| Tingo María | -9.2985 | -75.9979 | Huánuco, Pucallpa |
| Pucallpa | -8.3791 | -74.5539 | Tingo María, Puerto Maldonado |
| Puerto Maldonado | -12.5933 | -69.1891 | Cusco, Pucallpa |
| Abancay | -13.6355 | -72.8814 | Cusco, Ayacucho |
| Moquegua | -17.1929 | -70.9320 | Arequipa, Puno, Tacna |
| Tacna | -18.0066 | -70.2462 | Moquegua |
| Nazca | -14.8294 | -74.9411 | Ica, Arequipa |
| Juliaca | -15.4997 | -70.1322 | Puno, Cusco |
| Huacho | -11.1072 | -77.6053 | Lima |

### Funciones utilitarias de `data.py`

```python
get_grafo()              # → {nodo: {vecino: peso_km}}
get_adyacentes(prov)     # → {vecino: distancia_km}
get_coords(prov)         # → (lat, lon)
```

---

## Fórmula de Haversine

Implementada en `utils.py`. Calcula la **distancia en línea recta** (gran círculo) entre dos puntos geográficos dados como `(lat, lon)` en grados decimales.

```
a = sin²(Δlat/2) + cos(lat₁) · cos(lat₂) · sin²(Δlon/2)
d = 2R · arcsin(√a)       donde R = 6371 km
```

Esta distancia es siempre **≤ distancia real por carretera**, por lo que constituye una **heurística admisible** (nunca sobreestima) para los algoritmos A\* y Greedy BFS.

```python
from utils import haversine

d = haversine((-12.0464, -77.0428), (-15.8402, -70.0219))
# Lima → Puno en línea recta ≈ 860 km
```

---

## Algoritmos Implementados

### 1. Dijkstra (`dijkstra.py`)

Algoritmo de referencia para grafos con pesos no negativos. Expande siempre el nodo con menor coste acumulado `g(n)`.

- **Estructura:** min-heap (`heapq`)
- **Complejidad:** O((V + E) log V)
- **Garantiza óptimo:** ✅ Sí
- **Heurística:** No
- **Firma:** `dijkstra(grafo, origen, destino, coords=None)`

```python
# Ejemplo de uso
from dijkstra import dijkstra
from data import get_grafo

dist, camino = dijkstra(get_grafo(), "Lima", "Puno")
# → (1072.0, ['Lima', 'Ica', 'Arequipa', 'Puno'])
```

### 2. A\* (`a_star.py`)

Extiende Dijkstra con una heurística `h(n)` que estima el coste restante al destino. Ordena el heap por `f(n) = g(n) + h(n)`.

- **Estructura:** min-heap ordenado por `f = g + h`
- **Complejidad:** O(E log V) promedio con buena heurística
- **Garantiza óptimo:** ✅ Sí (con heurística admisible)
- **Heurística:** ✅ Haversine
- **Firma:** `astar(grafo, origen, destino, coords)`

La heurística Haversine es admisible porque la distancia en línea recta siempre es menor o igual a la distancia real por carretera, lo que garantiza que A\* nunca descarta el camino óptimo.

### 3. Bellman-Ford (`bellman_ford.py`)

Relaja todas las aristas del grafo `V-1` veces. Capaz de manejar pesos negativos y detectar ciclos negativos.

- **Estructura:** lista de aristas + iteración
- **Complejidad:** O(V · E)
- **Garantiza óptimo:** ✅ Sí
- **Heurística:** No
- **Detección de ciclos negativos:** ✅ Sí (V-ésima pasada)
- **Optimización:** convergencia temprana si no hay actualizaciones

```
for _ in range(V - 1):
    for cada arista (u, v, peso):
        si dist[u] + peso < dist[v]:
            relajar
```

### 4. Dijkstra Bidireccional (`bidireccional.py`)

Ejecuta dos búsquedas simultáneas: una desde el origen y otra desde el destino sobre el grafo inverso. Se detiene cuando ambas fronteras se encuentran.

- **Estructura:** dos min-heaps independientes
- **Complejidad:** O((V + E) log V) con constante ~2x menor que Dijkstra
- **Garantiza óptimo:** ✅ Sí
- **Heurística:** No
- **Grafo inverso:** construido automáticamente invirtiendo las aristas
- **Criterio de parada:** `min_f + min_b >= mejor_distancia_conocida`

La reconstrucción del camino une las dos mitades: `segmento_f` (origen → nodo_medio) y `segmento_b` (nodo_medio → destino).

### 5. Greedy Best-First Search (`greedy_bfs.py`)

Expande siempre el nodo con menor valor heurístico `h(n)`, ignorando el coste acumulado `g(n)`. Más rápido que A\*, pero **no garantiza optimalidad**.

- **Estructura:** min-heap ordenado solo por `h`
- **Complejidad:** O(E log V) promedio
- **Garantiza óptimo:** ⚠️ No necesariamente
- **Heurística:** ✅ Haversine
- **Uso pedagógico:** ilustra claramente la diferencia entre búsqueda informada óptima (A\*) y no óptima (Greedy)

> La distancia retornada es el coste **real** del camino encontrado, no la estimación heurística.

### 6. Floyd-Warshall (`floyd_warshall.py`)

Calcula la ruta mínima entre **todos los pares** de nodos en una sola ejecución usando programación dinámica con triple bucle anidado.

- **Estructura:** matrices de distancias y predecesores `V×V`
- **Complejidad:** O(V³) tiempo, O(V²) espacio
- **Garantiza óptimo:** ✅ Sí (para todos los pares)
- **Heurística:** No
- **Firma especial:** `floyd_warshall(grafo, origen=None, destino=None)`
  - Sin origen/destino → retorna matrices completas `(dist, prev)`
  - Con origen/destino → retorna `(distancia, camino)` para ese par

```
dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
```

La reconstrucción de camino usa la matriz `prev[u][v]` que almacena el predecesor inmediato en la ruta óptima de `u` a `v`.

### 7. Uniform Cost Search — UCS (`ucs.py`)

Dijkstra reformulado como búsqueda en árbol: expande el nodo de menor coste acumulado y aplica el **goal test al expandir** (no al insertar). Marca nodos como "cerrados" en lugar de actualizar un array global de distancias.

- **Estructura:** min-heap + conjunto de nodos cerrados
- **Complejidad:** O((V + E) log V)
- **Garantiza óptimo:** ✅ Sí
- **Heurística:** No
- **Diferencia con Dijkstra:** paradigma de búsqueda en árbol vs. relajación de aristas

---

## Arquitectura de la Aplicación

### Flujo de datos

```
data.py
  └── get_grafo()  ──────────────────────────────┐
  └── get_coords() ──────────────────────────────┤
  └── get_adyacentes() ──── app.py (UI sidebar)  │
                                                  ▼
utils.py                                  algorithms.py
  └── haversine()  ◄──── a_star.py            ├── dijkstra
  └── reconstruir_camino() ◄── todos           ├── astar
                                               ├── bellman_ford
app.py (resultados)                            ├── bidireccional
  └── tabla comparativa                        ├── greedy_bfs
  └── detalle de caminos                       ├── floyd_warshall
  └── gráfico de tiempos                       └── ucs
```

### Firma uniforme de todos los algoritmos

Para que `app.py` pueda iterar sobre los algoritmos de forma genérica, todos comparten la misma firma:

```python
def algoritmo(
    grafo: dict[str, dict[str, float]],
    origen: str,
    destino: str,
    coords: dict[str, tuple[float, float]] | None = None,
) -> tuple[float | None, list[str] | None]:
    ...
    return distancia_total_km, lista_de_nodos
```

Floyd-Warshall tiene una firma extendida para soportar también el modo de matrices completas, pero `app.py` lo invoca con origen y destino para mantener consistencia.

### Medición de tiempo

```python
inicio  = time.perf_counter()          # resolución de microsegundos
dist, camino = func(grafo, origen, destino, coords)
fin     = time.perf_counter()
elapsed = (fin - inicio) * 1_000       # convertir a milisegundos
```

Se usa `time.perf_counter()` (no `time.time()`) para obtener la mayor resolución posible del sistema operativo.

---

## Instalación y Uso

### Requisitos

```
Python >= 3.10
streamlit
pandas
```

### Instalación

```bash
git clone <repo>
cd rutas-peru

pip install streamlit pandas
```

### Ejecución

```bash
streamlit run app.py
```

La aplicación abre automáticamente en `http://localhost:8501`.

### Uso de la interfaz

1. En el **panel lateral**, selecciona la provincia de **Origen** y **Destino** desde los dropdowns.
2. Activa o desactiva los algoritmos con los **checkboxes**.
3. Pulsa **"Calcular Rutas"**.
4. Revisa:
   - La **tabla comparativa** con distancia, pasos y tiempo de ejecución.
   - El **detalle de caminos** con los nodos de cada ruta (el óptimo aparece resaltado en verde 🏆).
   - El **gráfico de barras** comparando tiempos de ejecución en ms.

---

## Comparativa de Algoritmos

| Algoritmo | Óptimo | Heurística | Complejidad | Mejor caso de uso |
|---|---|---|---|---|
| Dijkstra | ✅ | No | O((V+E) log V) | Referencia general |
| A\* | ✅ | ✅ Haversine | O(E log V) prom. | Grafos geográficos grandes |
| Bellman-Ford | ✅ | No | O(V·E) | Grafos con pesos negativos |
| Bidireccional | ✅ | No | ~½ Dijkstra | Grafos simétricos grandes |
| Greedy BFS | ⚠️ | ✅ Haversine | O(E log V) prom. | Búsqueda rápida no crítica |
| Floyd-Warshall | ✅ | No | O(V³) | Múltiples consultas al mismo grafo |
| UCS | ✅ | No | O((V+E) log V) | Paradigma de búsqueda en árbol |

### ¿Cuándo usar cada uno?

- **Dijkstra / UCS:** consultas únicas sobre grafos medianos con pesos positivos. UCS es conceptualmente más limpio para implementaciones educativas.
- **A\*:** cuando se dispone de coordenadas geográficas; reduce significativamente los nodos explorados gracias a la heurística Haversine.
- **Bellman-Ford:** cuando el grafo puede tener aristas negativas o se necesita detección de ciclos negativos.
- **Bidireccional:** útil en grafos grandes y simétricos; reduce el espacio de búsqueda a la raíz cuadrada del área explorada por Dijkstra.
- **Greedy BFS:** cuando la velocidad prima sobre la optimalidad; puede encontrar una ruta razonable más rápido que A\*.
- **Floyd-Warshall:** ideal cuando se necesitan respuestas para muchos pares origen-destino; el coste O(V³) se amortiza entre todas las consultas.

---

## Ejemplos de Resultados

### Lima → Puno

| Algoritmo | Distancia | Pasos | Ruta |
|---|---|---|---|
| Dijkstra | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |
| A\* | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |
| Bellman-Ford | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |
| Bidireccional | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |
| Greedy BFS | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |
| Floyd-Warshall | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |
| UCS | 1 072 km | 3 | Lima → Ica → Arequipa → Puno |

### Lima → Cusco

| Algoritmo | Distancia | Pasos | Ruta |
|---|---|---|---|
| Dijkstra | 1 088 km | 4 | Lima → Huancayo → Ayacucho → Abancay → Cusco |
| A\* | 1 088 km | 4 | Lima → Huancayo → Ayacucho → Abancay → Cusco |
| Greedy BFS | 1 145 km | 3 | Lima → Huancayo → Ayacucho → Cusco ⚠️ |
| Floyd-Warshall | 1 088 km | 4 | Lima → Huancayo → Ayacucho → Abancay → Cusco |

> Greedy BFS elige la ruta de 3 pasos porque cada paso parece acercarse más al destino según Haversine, pero el resultado final es 57 km más largo.

### Tacna → Pucallpa (ruta más exigente)

Todos los algoritmos óptimos convergen en:

```
Tacna → Moquegua → Arequipa → Ica → Lima → Cerro de Pasco → Huánuco → Tingo María → Pucallpa
1 944 km · 8 pasos
```

---

## Decisiones de Diseño

### Pesos por carretera, heurística por Haversine

Los pesos de las aristas reflejan **distancias reales por carretera** (más largas que la línea recta). La heurística Haversine calcula la distancia en línea recta y por tanto **siempre subestima** el coste real, garantizando admisibilidad para A\*.

### Grafo no dirigido simétrico

Todas las aristas están duplicadas en ambas direcciones en `data.py` con el mismo peso, lo que simplifica la construcción del grafo inverso para el algoritmo bidireccional y refleja la realidad de carreteras bidireccionales.

### Módulo `algorithms.py` como fachada

`app.py` importa únicamente desde `algorithms.py`. Esto desacopla la UI de los archivos individuales: añadir un nuevo algoritmo solo requiere crear su archivo e importarlo en `algorithms.py`, sin tocar `app.py`.

### Floyd-Warshall con firma dual

El algoritmo soporta dos modos de uso mediante parámetros opcionales:

```python
# Modo par (desde app.py)
dist, camino = floyd_warshall(grafo, "Lima", "Puno")

# Modo completo (para análisis avanzado)
dist_matrix, prev_matrix = floyd_warshall(grafo)
```

### Degradación elegante sin `algorithms.py`

Si `algorithms.py` no existe (desarrollo incremental), `app.py` carga stubs que devuelven `(None, None)` y la UI permanece funcional, mostrando "Sin implementar" en lugar de lanzar excepciones.

---

## Contexto Académico

Este proyecto forma parte del análisis de algoritmos de grafos aplicados a datos geoespaciales reales del Perú. La elección de provincias con coordenadas GPS reales y distancias por carretera aproximadas permite validar empíricamente el comportamiento diferencial de cada algoritmo (optimalidad, velocidad de convergencia, nodos explorados) sobre un grafo con estructura geográfica real.
>>>>>>> ce449e8 (Primera versión del proyecto TINKUY)
