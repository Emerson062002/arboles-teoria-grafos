"""Adaptador de consola y lector opcional de grafos desde archivos."""

import argparse
from pathlib import Path
from typing import Optional

from ..application.ports import AnalyzeGraphPort
from ..application.use_cases import AnalyzeGraph

SAMPLE_EDGES = [
    ("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5),
    ("C", "D", 8), ("C", "E", 10), ("D", "E", 2),
]


def read_graph(path):
    """Lee aristas con formato `origen, destino, peso`, una por línea."""
    edges = []
    for line_number, raw_line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 3 or not fields[0] or not fields[1]:
            raise ValueError(f"La línea {line_number} debe tener el formato: origen, destino, peso.")
        try:
            weight = float(fields[2])
        except ValueError as error:
            raise ValueError(f"El peso de la línea {line_number} no es un número válido.") from error
        if weight.is_integer():
            weight = int(weight)
        edges.append((fields[0], fields[1], weight))
    return edges


def display_result(name, result):
    print(f"\n{name}")
    print(f"Aristas: {[f'{edge.desde}{edge.hasta}' for edge in result.edges]}")
    print(f"Peso total: {result.total_weight}")
    print(
        f"Componentes: {result.components} · "
        f"examinadas: {result.stats['edges_examined']} · "
        f"agregadas: {result.stats['edges_selected']} · "
        f"descartadas: {result.stats['edges_rejected']} · "
        f"complejidad: {result.stats['complexity']}"
    )
    if result.connected:
        print(f"Comprobación: {result.vertices_count} vértices, "
              f"{len(result.edges)} aristas, conexo -> es un árbol")
    else:
        print("El grafo no es conexo; el resultado es un bosque mínimo.")


def main(analyzer: Optional[AnalyzeGraphPort] = None, argv=None):
    parser = argparse.ArgumentParser(description="Analiza un grafo con Kruskal y Prim.")
    parser.add_argument("archivo", nargs="?", help="Archivo con aristas: origen, destino, peso")
    arguments = parser.parse_args(argv)
    edges = read_graph(arguments.archivo) if arguments.archivo else SAMPLE_EDGES
    vertices = list(dict.fromkeys(vertex for edge in edges for vertex in edge[:2]))
    if not vertices:
        raise ValueError("El archivo debe contener al menos una arista.")
    analysis = (analyzer or AnalyzeGraph()).execute(edges, vertices)

    print("Pasos de Kruskal:")
    for step in analysis.kruskal.steps:
        print(f"{step.desde}{step.hasta:<6}{step.peso:<8}{step.detalle}")
    display_result("Resultado de Kruskal", analysis.kruskal)
    display_result("Comparación con Prim", analysis.prim)
    print("\nCuello de botella y cortaduras")
    if analysis.peso_cuello_botella is None:
        print("Cuello de botella: no hay aristas seleccionadas.")
    else:
        bottlenecks = ", ".join(
            f"{edge.desde}{edge.hasta} ({edge.peso})"
            for edge in analysis.cuello_botella
        )
        print(f"Cuello de botella (peso {analysis.peso_cuello_botella}): {bottlenecks}")
    bridges = ", ".join(
        f"{edge.desde}{edge.hasta}" for edge in analysis.cortaduras.puentes
    ) or "ninguno"
    articulation_vertices = ", ".join(
        analysis.cortaduras.vertices_articulacion
    ) or "ninguno"
    print(f"Puentes: {bridges}")
    print(f"Vértices de articulación: {articulation_vertices}")


if __name__ == "__main__":
    main()
