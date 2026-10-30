"""Casos de uso que coordinan las reglas del dominio."""

from math import isclose

from ..domain.grafo import Grafo
from ..domain.kruskal import kruskal
from ..domain.prim import prim
from ..domain.resultado import Comparacion


class AnalyzeGraph:
    """Calcula resultados comparables de Kruskal y Prim."""

    def execute(self, edges, vertices=None) -> Comparacion:
        graph = Grafo.crear(edges, vertices)
        kruskal_result = kruskal(graph)
        prim_result = prim(graph)
        return Comparacion(
            kruskal=kruskal_result,
            prim=prim_result,
            pesos_iguales=isclose(
                kruskal_result.total_weight,
                prim_result.total_weight,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
        )
