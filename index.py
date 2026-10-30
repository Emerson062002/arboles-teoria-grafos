"""Punto de entrada compatible para la consola y las pruebas existentes."""

from kruskal_app.adapters.console import SAMPLE_EDGES, main
from kruskal_app.domain.grafo import Grafo
from kruskal_app.domain.kruskal import kruskal as _kruskal
from kruskal_app.domain.union_find import UnionFind

ARISTAS = SAMPLE_EDGES


def kruskal(aristas, vertices=None):
    """Mantiene la interfaz histórica de la función de Kruskal."""
    result = _kruskal(Grafo.crear(aristas, vertices))
    steps = [
        (
            f"{step.desde}{step.hasta}",
            step.peso,
            "Se agrega" if step.agrega else "Se descarta (cerraría un ciclo)",
        )
        for step in result.steps
    ]
    return (
        [(edge.desde, edge.hasta, edge.peso) for edge in result.edges],
        steps,
        result.vertices_count,
    )


def es_conexo(vertices, aristas):
    """Mantiene la interfaz histórica de la comprobación de conectividad."""
    vertices = list(vertices)
    if not vertices:
        return False
    union_find = UnionFind(vertices)
    for edge in aristas:
        union_find.unir(edge[0], edge[1])
    return len({union_find.encontrar(vertex) for vertex in vertices}) == 1


if __name__ == "__main__":
    main()
