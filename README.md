# 🗺️ Rutas Cortas entre Provincias del Perú

Aplicación interactiva desarrollada en **Python + Streamlit** que implementa y compara **7 algoritmos clásicos de camino mínimo** sobre un grafo geoespacial real construido a partir de los datos oficiales de las 196 provincias del Perú.

> **Proyecto NIVARI** — Detección de heladas en Puno, Perú.

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
- [Algoritmos Implementados](#algoritmos-implementados)
- [Interfaz de la Aplicación](#interfaz-de-la-aplicación)
- [Comparativa de Algoritmos](#comparativa-de-algoritmos)

---

## Visión General

El territorio peruano se modela como un **grafo no dirigido ponderado** donde:

- Cada **nodo** es una provincia, con su centroide geográfico real (latitud/longitud).
- Cada **arista** conecta dos provincias colindantes, con peso igual a la distancia en línea recta entre sus centroides (fórmula de Haversine, en km).
- Los **7 algoritmos** se ejecutan sobre el mismo grafo y sus resultados se comparan en tiempo real: distancia encontrada, pasos recorridos y tiempo de ejecución en milisegundos.

---

## Estructura del Proyecto

```
TINKUY/
│
├── peru_provincial_simple.geojson   ← Fuente de datos (IGN, 196 provincias)
│
├── generar_grafo.py                 ← Preprocesamiento: GeoJSON → JSON
├── grafo_completo.json              ← Grafo generado (196 nodos, ~800 conexiones)
│
├── data.py                          ← Carga el JSON y expone la API de datos
├── utils.py                         ← Haversine + reconstrucción de caminos
│
├── algorithms.py                    ← Punto de entrada unificado de algoritmos
├── dijkstra.py
├── a_star.py
├── bellman_ford.py
├── bidireccional.py
├── greedy_bfs.py
├── floyd_warshall.py
├── ucs.py
│
└── app.py                           ← Interfaz Streamlit
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

## Algoritmos Implementados

Todos reciben el mismo grafo y devuelven la distancia total en km y la lista de provincias del camino encontrado. Retornan `None` si no existe ruta.

### Dijkstra
Expande siempre el nodo de menor distancia acumulada usando un min-heap. Garantiza la ruta óptima para grafos con pesos no negativos. Es el algoritmo de referencia del proyecto. **Complejidad:** O((V+E) log V).

### A\* (A-estrella)
Extiende Dijkstra añadiendo una heurística que estima el coste restante al destino usando Haversine. Al ordenar por `f = g + h` (coste real + estimación), se dirige hacia el destino explorando menos nodos que Dijkstra sin sacrificar optimalidad. **Complejidad:** O(E log V) promedio.

### Bellman-Ford
Relaja todas las aristas del grafo V−1 veces. Más lento que Dijkstra pero capaz de manejar pesos negativos y detectar ciclos negativos. Incluye una optimización de convergencia temprana. **Complejidad:** O(V·E).

### Dijkstra Bidireccional
Lanza dos búsquedas simultáneas: una desde el origen y otra desde el destino sobre el grafo inverso. Se detiene cuando la suma de los mínimos de ambas fronteras supera la mejor distancia conocida. Más eficiente en grafos grandes. **Complejidad:** ~½ Dijkstra en la práctica.

### Greedy Best-First Search
Ordena el heap únicamente por la heurística Haversine, ignorando el coste acumulado. Es el más rápido pero no garantiza la ruta óptima: prioriza lo que parece más cerca al destino en línea recta, sin considerar el camino ya recorrido. **Complejidad:** O(E log V) promedio.

### Floyd-Warshall
Calcula la ruta mínima entre **todos los pares** de nodos en una sola ejecución mediante programación dinámica. El coste O(V³) se amortiza cuando se necesitan múltiples consultas sobre el mismo grafo. **Complejidad:** O(V³) tiempo, O(V²) espacio.

### UCS (Uniform Cost Search)
Reformulación de Dijkstra bajo el paradigma de búsqueda en árbol: aplica el test de llegada al expandir (no al insertar) y mantiene un conjunto explícito de nodos cerrados. Produce resultados idénticos a Dijkstra. **Complejidad:** O((V+E) log V).

---

## Interfaz de la Aplicación

La interfaz usa `layout="wide"` con un sidebar de controles y un área principal organizada en tres pestañas.

**Sidebar:** selectores de provincia de origen y destino (las 196 cargadas del JSON), multiselect de algoritmos, visor de provincias adyacentes y botón de ejecución.

**🗺️ Mapa Interactivo:** Mapa Pydeck con cinco capas superpuestas — los polígonos provinciales como fondo (GeoJsonLayer), los 196 nodos, las líneas de la ruta óptima en rojo, los nodos del camino diferenciados por color (ámbar para el origen, verde para el destino, azul para intermedios) y etiquetas sobre cada nodo del recorrido. Bajo el mapa se muestran tres métricas del algoritmo ganador: distancia total, tiempo de ejecución y nodos recorridos.

**📊 Tabla Comparativa:** Tarjetas por algoritmo con código de color — verde para la ruta óptima, amarillo para resultados subóptimos y rojo si no se encontró ruta.

**⏱️ Rendimiento:** Gráficos de barras de tiempos y distancias por algoritmo, y tabla de análisis de suboptimalidad con el exceso en km y porcentaje respecto a la ruta óptima.

---

## Comparativa de Algoritmos

| Algoritmo | Óptimo | Heurística | Complejidad | Cuándo usarlo |
|---|---|---|---|---|
| Dijkstra | ✅ | No | O((V+E) log V) | Caso general, referencia |
| A\* | ✅ | ✅ Haversine | O(E log V) prom. | Grafos geográficos, más rápido |
| Bellman-Ford | ✅ | No | O(V·E) | Si hubiera pesos negativos |
| Bidireccional | ✅ | No | ~½ Dijkstra | Grafos grandes y simétricos |
| Greedy BFS | ⚠️ | ✅ Haversine | O(E log V) prom. | Aproximación rápida |
| Floyd-Warshall | ✅ | No | O(V³) | Múltiples consultas al mismo grafo |
| UCS | ✅ | No | O((V+E) log V) | Paradigma de búsqueda en árbol (IA) |

---

## Repositorio

🔗 [https://github.com/Jhyna-Shady/TINKUY](https://github.com/Jhyna-Shady/TINKUY)
