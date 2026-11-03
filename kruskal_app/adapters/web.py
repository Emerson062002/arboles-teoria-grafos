"""HTTP adapter for the graph explorer and its private analysis history."""

import argparse
import json
from dataclasses import asdict
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import urlparse

from ..application.ports import AnalyzeGraphPort
from ..application.use_cases import AnalyzeGraph
from .analysis_repository import AnalysisRepository, AnalysisStorageError
from .auth import AuthSettings, SESSION_COOKIE, SESSION_MAX_AGE

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_REQUEST_SIZE = 1_000_000


class GraphRequestHandler(BaseHTTPRequestHandler):
    """Translate HTTP requests into graph analysis and history operations."""

    analyzer: AnalyzeGraphPort = AnalyzeGraph()
    repository = None

    def _auth_settings(self):
        return AuthSettings.from_environment()

    def _session_token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except CookieError:
            return ""
        morsel = cookie.get(SESSION_COOKIE)
        return morsel.value if morsel else ""

    def _is_authenticated(self, settings):
        return not settings.enabled or settings.is_valid_session(self._session_token())

    def _require_authentication(self, settings):
        if self._is_authenticated(settings):
            return True
        self._send_json(401, {"error": "Inicia sesión para continuar."})
        return False

    def _require_same_origin(self, settings):
        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        parsed_origin = urlparse(origin or "")
        forwarded_scheme = self.headers.get("X-Forwarded-Proto", "").split(",", 1)[0].strip()
        expected_scheme = forwarded_scheme or (
            "https" if settings.secure_cookie else "http"
        )
        if (
            parsed_origin.scheme.casefold() != expected_scheme.casefold()
            or parsed_origin.netloc.casefold() != host.casefold()
            or parsed_origin.path not in ("", "/")
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            self._send_json(403, {"error": "Solicitud de origen no permitido."})
            return False
        return True

    def _get_repository(self):
        if self.repository is None:
            self.__class__.repository = AnalysisRepository.from_environment()
        return self.repository

    def _serve_asset(self, asset_name):
        content = (PROJECT_ROOT / "kruskal_app" / "web" / asset_name).read_bytes()
        self.send_response(200)
        content_type = guess_type(asset_name)[0] or "application/octet-stream"
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        settings = self._auth_settings()

        if path == "/api/session":
            self._send_json(200, {
                "authentication_required": settings.enabled,
                "authenticated": self._is_authenticated(settings),
            })
            return

        if path == "/login":
            if self._is_authenticated(settings):
                self._redirect("/")
            else:
                self._serve_asset("login.html")
            return

        if path in ("/", "/index.html"):
            if not self._is_authenticated(settings):
                self._redirect("/login")
                return
            self._serve_asset("index.html")
            return

        if path == "/app.js" and not self._require_authentication(settings):
            return

        asset_name = {
            "/style.css": "style.css",
            "/app.js": "app.js",
            "/login.js": "login.js",
        }.get(path)
        if asset_name:
            self._serve_asset(asset_name)
            return

        if path == "/api/history":
            if not self._require_authentication(settings):
                return
            try:
                history = self._get_repository().recent()
            except AnalysisStorageError as error:
                print(f"No se pudo consultar el historial: {error}")
                self._send_json(503, {"error": "No se pudo consultar el historial guardado."})
                return
            self._send_json(200, {"history": history})
            return

        self._send_json(404, {"error": "Ruta no encontrada."})

    def do_POST(self):
        path = urlparse(self.path).path
        settings = self._auth_settings()
        if path == "/api/login":
            self._handle_login(settings)
            return
        if path == "/api/logout":
            if not self._require_same_origin(settings) or not self._require_authentication(settings):
                return
            self._send_json(200, {"ok": True}, self._clear_session_cookie(settings))
            return
        if path != "/api/analyze":
            self._send_json(404, {"error": "Ruta no encontrada."})
            return
        if not self._require_same_origin(settings) or not self._require_authentication(settings):
            return

        try:
            payload = self._read_json()
            edges, vertices, should_save = self._parse_graph_payload(payload)
            analysis = asdict(self.analyzer.execute(edges, vertices))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return

        if should_save:
            try:
                record_id = self._get_repository().save(vertices, edges, analysis)
            except AnalysisStorageError as error:
                print(f"No se pudo guardar el análisis: {error}")
                self._send_json(
                    503, {"error": "No se pudo guardar el análisis en el historial."}
                )
                return
            analysis["analysis_id"] = record_id
        self._send_json(200, analysis)

    def _handle_login(self, settings):
        if not self._require_same_origin(settings):
            return
        if not settings.enabled:
            self._send_json(404, {"error": "El inicio de sesión no está configurado."})
            return
        try:
            payload = self._read_json()
            if not isinstance(payload, dict):
                raise ValueError("Envía usuario y contraseña.")
            username = payload.get("username")
            password = payload.get("password")
            if not isinstance(username, str) or not isinstance(password, str):
                raise ValueError("Envía usuario y contraseña.")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return

        if not settings.authenticate(username, password):
            self._send_json(401, {"error": "Usuario o contraseña incorrectos."})
            return
        self._send_json(
            200,
            {"ok": True},
            self._session_cookie(settings, settings.create_session()),
        )

    def _read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError as error:
            raise ValueError("El tamaño de la solicitud no es válido.") from error
        if not 0 < content_length <= MAX_REQUEST_SIZE:
            raise ValueError("El tamaño de la solicitud no es válido.")
        return json.loads(self.rfile.read(content_length).decode("utf-8"))

    @staticmethod
    def _parse_graph_payload(payload):
        if not isinstance(payload, dict) or not isinstance(payload.get("edges"), list):
            raise ValueError("Envía una lista de aristas y una lista de vértices.")
        should_save = payload.get("save", True)
        if not isinstance(should_save, bool):
            raise ValueError("La opción de guardar el análisis no es válida.")
        vertices = payload.get("vertices")
        if vertices is not None and not isinstance(vertices, list):
            raise ValueError("La lista de vértices no es válida.")
        edges = []
        for line_number, edge in enumerate(payload["edges"], start=1):
            if not isinstance(edge, list) or len(edge) != 3:
                raise ValueError(
                    f"La línea {line_number} debe tener el formato: origen, destino, peso."
                )
            source, target, weight = edge
            if isinstance(weight, str):
                try:
                    weight = float(weight)
                except ValueError as error:
                    raise ValueError(
                        f"El peso de la línea {line_number} no es un número válido."
                    ) from error
            edges.append((source, target, weight))
        return edges, vertices, should_save

    def _session_cookie(self, settings, value):
        parts = [
            f"{SESSION_COOKIE}={value}",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            f"Max-Age={SESSION_MAX_AGE}",
        ]
        if settings.secure_cookie:
            parts.append("Secure")
        return "; ".join(parts)

    def _clear_session_cookie(self, settings):
        parts = [f"{SESSION_COOKIE}=", "Path=/", "HttpOnly", "SameSite=Strict", "Max-Age=0"]
        if settings.secure_cookie:
            parts.append("Secure")
        return "; ".join(parts)

    def _redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, status, payload, set_cookie=None):
        content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def serve(host="127.0.0.1", port=8000):
    AuthSettings.from_environment()
    GraphRequestHandler.repository = AnalysisRepository.from_environment()
    server = ThreadingHTTPServer((host, port), GraphRequestHandler)
    print(f"Interfaz disponible en http://{host}:{server.server_port}")
    print("Presiona Ctrl+C para detener el servidor.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inicia la interfaz web de Kruskal.")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Dirección donde escucha el servidor (127.0.0.1 solo local; 0.0.0.0 red local).",
    )
    parser.add_argument("--port", type=int, default=8000, help="Puerto HTTP (por defecto: 8000).")
    arguments = parser.parse_args(argv)
    serve(arguments.host, arguments.port)


if __name__ == "__main__":
    main()
