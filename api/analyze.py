from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            url = data.get('url')

            if not url:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Debes ingresar una URL"}).encode('utf-8'))
                return

            if not url.startswith('http'):
                url = 'https://' + url

            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else 'Sin título'

            results = {
                "url": url,
                "score": 100 if response.status_code == 200 else 50,
                "passed": ["Conexión exitosa"] if response.status_code == 200 else [],
                "failed": ["Error de conexión"] if response.status_code != 200 else [],
                "title": title
            }

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_GET(self):
        self.send_response(405)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Método no permitido"}).encode('utf-8'))