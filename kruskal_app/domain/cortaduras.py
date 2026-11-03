"""Detección de puentes y vértices de articulación en grafos no dirigidos."""

from .grafo import Grafo
from .resultado import Cortaduras


def detectar_cortaduras(graph: Grafo) -> Cortaduras:
    """Encuentra puentes y vértices de articulación en tiempo O(V + E)."""
    adjacency = {vertex: [] for vertex in graph.vertices}
    for index, edge in enumerate(graph.aristas):
        adjacency[edge.desde].append((edge.hasta, index))
        adjacency[edge.hasta].append((edge.desde, index))

    discovery = {}
    low = {}
    parent = {}
    parent_edge = {}
    child_count = {vertex: 0 for vertex in graph.vertices}
    bridge_indices = set()
    articulation_vertices = set()
    clock = 0

    for root in graph.vertices:
        if root in discovery:
            continue
        discovery[root] = low[root] = clock
        clock += 1
        parent[root] = None
        stack = [(root, iter(adjacency[root]))]

        while stack:
            vertex, neighbors = stack[-1]
            try:
                neighbor, edge_index = next(neighbors)
            except StopIteration:
                stack.pop()
                predecessor = parent[vertex]
                if predecessor is None:
                    if child_count[vertex] > 1:
                        articulation_vertices.add(vertex)
                    continue

                low[predecessor] = min(low[predecessor], low[vertex])
                if low[vertex] > discovery[predecessor]:
                    bridge_indices.add(parent_edge[vertex])
                if parent[predecessor] is not None and low[vertex] >= discovery[predecessor]:
                    articulation_vertices.add(predecessor)
                continue

            if neighbor not in discovery:
                parent[neighbor] = vertex
                parent_edge[neighbor] = edge_index
                child_count[vertex] += 1
                discovery[neighbor] = low[neighbor] = clock
                clock += 1
                stack.append((neighbor, iter(adjacency[neighbor])))
            elif neighbor != parent[vertex]:
                low[vertex] = min(low[vertex], discovery[neighbor])

    return Cortaduras(
        puentes=[graph.aristas[index] for index in sorted(bridge_indices)],
        vertices_articulacion=[
            vertex for vertex in graph.vertices if vertex in articulation_vertices
        ],
    )
