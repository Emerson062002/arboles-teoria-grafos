import ast
from pathlib import Path
import unittest

from index import es_conexo, kruskal
from kruskal_app.application.use_cases import AnalyzeGraph
from kruskal_app.domain.grafo import Grafo
from kruskal_app.domain.kruskal import kruskal as domain_kruskal
from kruskal_app.domain.prim import prim


class KruskalTests(unittest.TestCase):
    def test_example_has_expected_minimum_tree(self):
        edges = [
            ("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5),
            ("C", "D", 8), ("C", "E", 10), ("D", "E", 2),
        ]
        tree, _, count = kruskal(edges)

        self.assertEqual(count, 5)
        self.assertEqual(sum(weight for _, _, weight in tree), 10)
        self.assertEqual(len(tree), count - 1)
        self.assertTrue(es_conexo(set("ABCDE"), tree))

    def test_equal_weights_produce_a_minimum_tree(self):
        tree, _, _ = kruskal([("A", "B", 1), ("B", "C", 1), ("A", "C", 1)])

        self.assertEqual(len(tree), 2)
        self.assertEqual(sum(weight for _, _, weight in tree), 2)

    def test_decimal_and_negative_weights_are_supported(self):
        tree, _, _ = kruskal([("A", "B", 2.5), ("B", "C", -1.5)])

        self.assertEqual(sum(weight for _, _, weight in tree), 1)

    def test_disconnected_graph_returns_minimum_forest(self):
        forest, _, count = kruskal([("A", "B", 2)], ["A", "B", "C"])

        self.assertEqual(count, 3)
        self.assertEqual(len(forest), 1)
        self.assertFalse(es_conexo(["A", "B", "C"], forest))

    def test_single_vertex_is_a_connected_tree(self):
        tree, steps, count = kruskal([], ["A"])

        self.assertEqual((tree, steps, count), ([], [], 1))
        self.assertTrue(es_conexo(["A"], tree))

    def test_isolated_vertices_are_preserved_in_the_forest(self):
        forest, _, count = kruskal([], ["A", "B", "C"])

        self.assertEqual(count - len(forest), 3)
        self.assertFalse(es_conexo(["A", "B", "C"], forest))

    def test_invalid_edges_raise_clear_errors(self):
        invalid_graphs = [
            ([("A", "B", 1)], ["A", "C"]),
            ([("A", "A", 1)], ["A"]),
            ([("A", "B", float("nan"))], ["A", "B"]),
            ([("A", "B", 1), ("B", "A", 2)], ["A", "B"]),
            ([("A", "B")], ["A", "B"]),
        ]
        for edges, vertices in invalid_graphs:
            with self.subTest(edges=edges):
                with self.assertRaises(ValueError):
                    kruskal(edges, vertices)

    def test_empty_graph_is_rejected(self):
        with self.assertRaises(ValueError):
            kruskal([], [])

    def test_prim_and_kruskal_find_equal_minimum_weight(self):
        edges = [
            ("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5),
            ("C", "D", 8), ("C", "E", 10), ("D", "E", 2),
        ]
        analysis = AnalyzeGraph().execute(edges, list("ABCDE"))

        self.assertEqual(analysis.kruskal.total_weight, 10)
        self.assertEqual(analysis.prim.total_weight, 10)
        self.assertTrue(analysis.pesos_iguales)
        self.assertEqual(len(analysis.kruskal.edges), 4)
        self.assertEqual(len(analysis.prim.edges), 4)
        self.assertTrue(analysis.kruskal.connected)
        self.assertTrue(analysis.prim.connected)

    def test_statistics_match_kruskal_steps(self):
        graph = Grafo.crear([
            ("A", "B", 1), ("B", "C", 2), ("A", "C", 3), ("C", "D", 4)
        ])
        result = domain_kruskal(graph)

        self.assertEqual(result.stats["edges_examined"], 4)
        self.assertEqual(result.stats["edges_selected"], 3)
        self.assertEqual(result.stats["edges_rejected"], 1)
        self.assertEqual(result.stats["complexity"], "O(E log E)")
        self.assertEqual(result.steps[0].componentes_restantes, 3)
        self.assertEqual(result.steps[0].peso_acumulado, 1)

    def test_use_case_reuses_generator_input_for_both_algorithms(self):
        edges = iter([("A", "B", 2), ("B", "C", 1)])

        analysis = AnalyzeGraph().execute(edges, iter(["A", "B", "C"]))

        self.assertEqual(analysis.kruskal.total_weight, 3)
        self.assertEqual(analysis.prim.total_weight, 3)

    def test_domain_does_not_depend_on_adapters(self):
        domain_path = Path(__file__).parents[1] / "domain"
        for source_path in domain_path.glob("*.py"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            imports = [
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            ]
            self.assertFalse(
                any(
                    dependency in imported
                    for imported in imports
                    for dependency in ("adapters", "application")
                ),
                f"{source_path.name} must not import application or adapters",
            )

    def test_prim_and_kruskal_return_equal_minimum_forests_when_disconnected(self):
        edges = [("A", "B", 2), ("C", "D", -1)]
        analysis = AnalyzeGraph().execute(edges, ["A", "B", "C", "D", "E"])

        self.assertEqual(analysis.kruskal.total_weight, 1)
        self.assertEqual(analysis.prim.total_weight, 1)
        self.assertEqual(analysis.kruskal.components, 3)
        self.assertEqual(analysis.prim.components, 3)
        self.assertFalse(analysis.kruskal.connected)
        self.assertFalse(analysis.prim.connected)

    def test_prim_handles_a_single_isolated_vertex(self):
        result = prim(Grafo.crear([], ["solo"]))

        self.assertEqual(result.edges, [])
        self.assertEqual(result.total_weight, 0)
        self.assertTrue(result.connected)


if __name__ == "__main__":
    unittest.main()
