import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from kruskal_app.adapters.web import GraphRequestHandler


class WebAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GraphRequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_get_serves_web_page(self):
        with urlopen(self.base_url) as response:
            page = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn('src="/app.js" defer></script>', page)
        with urlopen(f"{self.base_url}/style.css") as response:
            self.assertIn("text/css", response.headers["Content-Type"])
        with urlopen(f"{self.base_url}/app.js") as response:
            script = response.read().decode("utf-8")
        self.assertIn('fetch("/api/analyze"', script)

    def test_post_returns_both_algorithm_results(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({
                "vertices": ["A", "B", "C"],
                "edges": [["A", "B", 1], ["B", "C", 2]],
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request) as response:
            result = json.loads(response.read())

        self.assertEqual(result["kruskal"]["total_weight"], 3)
        self.assertEqual(result["prim"]["total_weight"], 3)
        self.assertEqual(result["kruskal"]["stats"]["edges_examined"], 2)
        self.assertEqual(result["peso_cuello_botella"], 2)
        self.assertEqual(
            [(edge["desde"], edge["hasta"]) for edge in result["cortaduras"]["puentes"]],
            [("A", "B"), ("B", "C")],
        )
        self.assertEqual(result["cortaduras"]["vertices_articulacion"], ["B"])

    def test_post_returns_a_clear_error_for_invalid_graphs(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({"vertices": ["A"], "edges": [["A", "A", 1]]}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as error:
            urlopen(request)

        self.assertEqual(error.exception.code, 400)
        self.assertIn("consigo mismo", error.exception.read().decode("utf-8"))
        error.exception.close()

    def test_post_accepts_weight_text_and_returns_progress_metadata(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({
                "vertices": ["A", "B"],
                "edges": [["A", "B", "2.5"]],
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request) as response:
            result = json.loads(response.read())

        self.assertEqual(result["kruskal"]["steps"][0]["peso_acumulado"], 2.5)
        self.assertEqual(result["kruskal"]["steps"][0]["componentes_restantes"], 1)
        self.assertTrue(result["pesos_iguales"])

    def test_post_reports_malformed_edge_with_line_number(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({
                "vertices": ["A", "B"],
                "edges": [["A", "B", "1", "extra"]],
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as error:
            urlopen(request)

        self.assertIn("línea 1", error.exception.read().decode("utf-8"))
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
