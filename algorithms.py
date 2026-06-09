# algorithms.py
# Punto de entrada unificado para todos los algoritmos de ruta corta.
# app.py importa desde aquí; esto desacopla la UI de los archivos individuales.

from dijkstra      import dijkstra        # noqa: F401
from a_star        import astar           # noqa: F401
from bellman_ford  import bellman_ford    # noqa: F401
from bidireccional import bidireccional   # noqa: F401
from greedy_bfs    import greedy_bfs      # noqa: F401
from floyd_warshall import floyd_warshall  # noqa: F401
from ucs           import ucs             # noqa: F401

__all__ = [
    "dijkstra",
    "astar",
    "bellman_ford",
    "bidireccional",
    "greedy_bfs",
    "floyd_warshall",
    "ucs",
]
