"""Modelo y validación de grafos ponderados no dirigidos."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Arista:
    desde: str
    hasta: str
    peso: Real


@dataclass(frozen=True)
class Grafo:
    vertices: List[str]
    aristas: List[Arista]

    @classmethod
    def crear(cls, aristas: Iterable[Tuple[str, str, Real]],
              vertices: Optional[Iterable[str]] = None):
        aristas = list(aristas)
        for index, edge in enumerate(aristas, start=1):
            if not isinstance(edge, (tuple, list)) or len(edge) != 3:
                raise ValueError(f"La arista {index} debe tener origen, destino y peso.")
            if any(not isinstance(vertex, str) or not vertex.strip() for vertex in edge[:2]):
                raise ValueError(f"Los extremos de la arista {index} deben ser nombres no vacíos.")

        vertex_list = (
            list(dict.fromkeys(vertex for edge in aristas for vertex in edge[:2]))
            if vertices is None else list(vertices)
        )
        if not vertex_list:
            raise ValueError("El grafo debe tener al menos un vértice.")
        if any(not isinstance(vertex, str) or not vertex.strip() for vertex in vertex_list):
            raise ValueError("Cada vértice debe ser un nombre de texto no vacío.")
        if len(set(vertex_list)) != len(vertex_list):
            raise ValueError("La lista de vértices contiene nombres repetidos.")

        vertex_set = set(vertex_list)
        seen_edges = set()
        validated_edges = []
        for index, (source, target, weight) in enumerate(aristas, start=1):
            if source not in vertex_set or target not in vertex_set:
                raise ValueError(f"La arista {index} usa un vértice no declarado.")
            if source == target:
                raise ValueError(f"La arista {index} conecta un vértice consigo mismo.")
            if isinstance(weight, bool) or not isinstance(weight, Real) or not isfinite(weight):
                raise ValueError(f"El peso de la arista {index} debe ser un número finito.")
            key = frozenset((source, target))
            if key in seen_edges:
                raise ValueError(f"La arista {index} está repetida.")
            seen_edges.add(key)
            validated_edges.append(Arista(source, target, weight))
        return cls(vertex_list, validated_edges)
