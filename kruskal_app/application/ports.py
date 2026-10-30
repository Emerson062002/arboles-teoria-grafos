"""Contratos que exponen las operaciones disponibles a los adaptadores."""

from typing import Protocol

from ..domain.resultado import Comparacion


class AnalyzeGraphPort(Protocol):
    """Puerto de entrada para comparar algoritmos sobre un grafo."""

    def execute(self, edges, vertices=None) -> Comparacion:
        """Valida el grafo y calcula sus bosques mínimos."""
