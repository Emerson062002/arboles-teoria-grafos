"""Implementación de Prim para árboles y bosques generadores mínimos."""

from heapq import heappop, heappush

from .grafo import Grafo
from .resultado import Paso, crear_resultado


def prim(graph):
    graph = graph if isinstance(graph, Grafo) else Grafo.crear(graph)
    adjacency = {vertex: [] for vertex in graph.vertices}
    for index, edge in enumerate(graph.aristas):
        adjacency[edge.desde].append((edge.peso, index, edge.hasta))
        adjacency[edge.hasta].append((edge.peso, index, edge.desde))

    visited = set()
    selected = []
    steps = []
    rejected = 0
    components_remaining = len(graph.vertices)
    accumulated_weight = 0
    for root in graph.vertices:
        if root in visited:
            continue
        visited.add(root)
        candidates = []
        for weight, index, target in adjacency[root]:
            heappush(candidates, (weight, index, root, target))
        while candidates:
            weight, index, source, target = heappop(candidates)
            if target in visited:
                rejected += 1
                steps.append(Paso(
                    indice=index, desde=source, hasta=target, peso=weight, agrega=False,
                    detalle=f"Se descarta: {target} ya pertenece al árbol en construcción.",
                    componentes_restantes=components_remaining,
                    peso_acumulado=accumulated_weight,
                ))
                continue
            visited.add(target)
            selected.append(graph.aristas[index])
            components_remaining -= 1
            accumulated_weight += weight
            steps.append(Paso(
                indice=index, desde=source, hasta=target, peso=weight, agrega=True,
                detalle=f"Se agrega: conecta {target} al árbol con el menor peso disponible.",
                componentes_restantes=components_remaining,
                peso_acumulado=accumulated_weight,
            ))
            for next_weight, next_index, next_target in adjacency[target]:
                if next_target not in visited:
                    heappush(
                        candidates, (next_weight, next_index, target, next_target)
                    )

    return crear_resultado(
        graph.vertices, selected, steps, rejected, "O(E log V)"
    )
