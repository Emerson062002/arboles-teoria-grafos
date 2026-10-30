"""Implementación de Kruskal y estadísticas de sus decisiones."""

from .grafo import Grafo
from .resultado import Paso, Resultado, crear_resultado
from .union_find import UnionFind


def kruskal(graph):
    graph = graph if isinstance(graph, Grafo) else Grafo.crear(graph)
    union_find = UnionFind(graph.vertices)
    selected = []
    steps = []
    rejected = 0
    components_remaining = len(graph.vertices)
    accumulated_weight = 0

    ordered_edges = sorted(enumerate(graph.aristas), key=lambda item: (item[1].peso, item[0]))
    for original_index, edge in ordered_edges:
        if len(selected) == len(graph.vertices) - 1:
            break
        accepted = union_find.unir(edge.desde, edge.hasta)
        if accepted:
            selected.append(edge)
            components_remaining -= 1
            accumulated_weight += edge.peso
            detail = f"Conecta {edge.desde} y {edge.hasta} sin crear un ciclo."
        else:
            rejected += 1
            detail = f"Se descarta: {edge.desde} y {edge.hasta} ya están conectados."
        steps.append(Paso(
            indice=original_index,
            desde=edge.desde,
            hasta=edge.hasta,
            peso=edge.peso,
            agrega=accepted,
            detalle=detail,
            componentes_restantes=components_remaining,
            peso_acumulado=accumulated_weight,
        ))
    return crear_resultado(graph.vertices, selected, steps, rejected, "O(E log E)")
