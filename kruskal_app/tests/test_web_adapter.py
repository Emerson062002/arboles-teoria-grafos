import json
import os
from http.cookiejar import CookieJar
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

from kruskal_app.adapters.analysis_repository import AnalysisRepository
from kruskal_app.adapters.web import GraphRequestHandler


class WebAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        environment_keys = (
            "APP_ENV", "APP_USERNAME", "APP_PASSWORD", "APP_SESSION_SECRET",
            "DATABASE_URL", "ANALYSIS_DB_PATH",
        )
        cls.environment = {key: os.environ.get(key) for key in environment_keys}
        os.environ.pop("APP_ENV", None)
        os.environ["APP_USERNAME"] = "owner"
        os.environ["APP_PASSWORD"] = "a-private-test-password"
        os.environ["APP_SESSION_SECRET"] = "test-session-secret-with-more-than-32-bytes"
        os.environ["ANALYSIS_DB_PATH"] = str(
            Path(cls.temporary_directory.name) / "history.sqlite3"
        )
        os.environ.pop("DATABASE_URL", None)
        GraphRequestHandler.repository = AnalysisRepository.from_environment()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GraphRequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.opener = build_opener(HTTPCookieProcessor(CookieJar()))
        request = Request(
            f"{cls.base_url}/api/login",
            data=json.dumps({
                "username": "owner",
                "password": "a-private-test-password",
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": cls.base_url,
            },
            method="POST",
        )
        with cls.opener.open(request) as response:
            if response.status != 200:
                raise RuntimeError("The test login could not be established.")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        GraphRequestHandler.repository = None
        for key, value in cls.environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        cls.temporary_directory.cleanup()

    def test_get_serves_web_page(self):
        with self.opener.open(self.base_url) as response:
            page = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn('src="/app.js" defer></script>', page)
        self.assertIn('id="history-list"', page)
        with self.opener.open(f"{self.base_url}/style.css") as response:
            self.assertIn("text/css", response.headers["Content-Type"])
        with self.opener.open(f"{self.base_url}/app.js") as response:
            script = response.read().decode("utf-8")
        self.assertIn('fetch("/api/analyze"', script)

    def test_post_returns_both_algorithm_results_and_saves_them(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({
                "vertices": ["A", "B", "C"],
                "edges": [["A", "B", 1], ["B", "C", 2]],
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )

        with self.opener.open(request) as response:
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
        self.assertIn("analysis_id", result)

    def test_post_returns_a_clear_error_for_invalid_graphs(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({"vertices": ["A"], "edges": [["A", "A", 1]]}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )

        with self.assertRaises(HTTPError) as error:
            self.opener.open(request)

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
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )

        with self.opener.open(request) as response:
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
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )

        with self.assertRaises(HTTPError) as error:
            self.opener.open(request)

        self.assertIn("línea 1", error.exception.read().decode("utf-8"))
        error.exception.close()

    def test_saved_analyses_are_available_in_private_history(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({
                "vertices": ["Ana", "Luis", "Marta"],
                "edges": [["Ana", "Luis", 3], ["Luis", "Marta", 7]],
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )
        with self.opener.open(request) as response:
            analysis = json.loads(response.read())

        with self.opener.open(f"{self.base_url}/api/history") as response:
            history = json.loads(response.read())["history"]

        saved = next(record for record in history if record["id"] == analysis["analysis_id"])
        self.assertEqual(saved["vertices"], ["Ana", "Luis", "Marta"])
        self.assertEqual(saved["analysis"]["kruskal"]["total_weight"], 10)
        persisted_history = AnalysisRepository(os.environ["ANALYSIS_DB_PATH"]).recent()
        self.assertTrue(any(record["id"] == analysis["analysis_id"] for record in persisted_history))

    def test_login_rejects_wrong_credentials(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar()))
        request = Request(
            f"{self.base_url}/api/login",
            data=json.dumps({"username": "owner", "password": "wrong-password"}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            opener.open(request)

        self.assertEqual(error.exception.code, 401)
        error.exception.close()

    def test_private_history_rejects_requests_without_a_valid_session(self):
        with urlopen(self.base_url) as response:
            self.assertIn("Iniciar sesión", response.read().decode("utf-8"))

        request = Request(
            f"{self.base_url}/api/history",
            headers={"Origin": self.base_url},
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(request)

        self.assertEqual(error.exception.code, 401)
        error.exception.close()

    def test_state_changing_requests_reject_cross_origin(self):
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({"vertices": ["A"], "edges": []}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": "https://malicious.example",
            },
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            self.opener.open(request)

        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_initial_page_calculation_can_skip_saving_history(self):
        repository = AnalysisRepository(os.environ["ANALYSIS_DB_PATH"])
        count_before = len(repository.recent(limit=1000))
        request = Request(
            f"{self.base_url}/api/analyze",
            data=json.dumps({
                "vertices": ["A", "B"],
                "edges": [["A", "B", 1]],
                "save": False,
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": self.base_url,
            },
            method="POST",
        )
        with self.opener.open(request) as response:
            result = json.loads(response.read())

        self.assertNotIn("analysis_id", result)
        self.assertEqual(len(repository.recent(limit=1000)), count_before)


if __name__ == "__main__":
    unittest.main()
