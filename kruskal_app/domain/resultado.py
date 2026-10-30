"""Resultados inmutables de los algoritmos de árbol generador mínimo."""

from dataclasses import dataclass
from typing import Dict, List, Sequence, Union

from .grafo import Arista


@dataclass(frozen=True)
class Paso:
    indice: int
    desde: str
    hasta: str
    peso: Union[int, float]
    agrega: bool
    detalle: str
    componentes_restantes: int
    peso_acumulado: Union[int, float]


@dataclass(frozen=True)
class Resultado:
    edges: List[Arista]
    steps: List[Paso]
    vertices_count: int
    edges_required: int
    connected: bool
    components: int
    total_weight: Union[int, float]
    stats: Dict[str, Union[int, str]]


@dataclass(frozen=True)
class Comparacion:
    kruskal: Resultado
    prim: Resultado
    pesos_iguales: bool


def crear_resultado(vertices, edges: Sequence[Arista], steps: Sequence[Paso],
                    rejected: int, complexity: str) -> Resultado:
    components = len(vertices) - len(edges)
    return Resultado(
        edges=list(edges),
        steps=list(steps),
        vertices_count=len(vertices),
        edges_required=max(len(vertices) - 1, 0),
        connected=components == 1,
        components=components,
        total_weight=sum((edge.peso for edge in edges), 0),
        stats={
            "edges_examined": len(steps),
            "edges_selected": len(edges),
            "edges_rejected": rejected,
            "complexity": complexity,
        },
    )
