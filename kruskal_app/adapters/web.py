"""Adaptador HTTP local para servir la web y consultar el caso de uso."""

import argparse
import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import urlparse

from ..application.ports import AnalyzeGraphPort
from ..application.use_cases import AnalyzeGraph

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_REQUEST_SIZE = 1_000_000


class GraphRequestHandler(BaseHTTPRequestHandler):
    """Traduce peticiones HTTP al puerto de análisis de grafos."""

    analyzer: AnalyzeGraphPort = AnalyzeGraph()

    def do_GET(self):
        asset_name = {
            "/": "index.html",
            "/index.html": "index.html",
            "/style.css": "style.css",
            "/app.js": "app.js",
        }.get(urlparse(self.path).path)
        if asset_name is None:
            self.send_error(404, "Ruta no encontrada.")
            return
        content = (PROJECT_ROOT / "kruskal_app" / "web" / asset_name).read_bytes()
        self.send_response(200)
        content_type = guess_type(asset_name)[0] or "application/octet-stream"
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if urlparse(self.path).path != "/api/analyze":
            self._send_json(404, {"error": "Ruta no encontrada."})
            return
        try:
            content_length = int(self.headers.get("Content-Length", ""))
            if not 0 < content_length <= MAX_REQUEST_SIZE:
                raise ValueError("El tamaño de la solicitud no es válido.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("edges"), list):
                raise ValueError("Envía una lista de aristas y una lista de vértices.")
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
            analysis = self.analyzer.execute(edges, vertices)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(200, asdict(analysis))

    def _send_json(self, status, payload):
        content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def serve(host="127.0.0.1", port=8000):
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
