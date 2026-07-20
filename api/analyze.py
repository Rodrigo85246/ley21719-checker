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

            # User-Agent para evitar bloqueos básicos de sitios
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, timeout=10, headers=headers)
            
            if response.status_code != 200:
                results = {
                    "url": url,
                    "score": 0,
                    "passed": [],
                    "failed": ["El sitio no respondió correctamente (Código: " + str(response.status_code) + ")"],
                    "title": "Sitio no accesible"
                }
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text().lower()
                title = soup.title.string.strip() if soup.title else 'Sin título'

                passed = []
                failed = []
                score = 0

                # 1. Política de Privacidad (40 puntos)
                if "política de privacidad" in text_content or "politica de privacidad" in text_content:
                    passed.append("Aviso de Política de Privacidad detectado")
                    score += 40
                else:
                    failed.append("No se detectó una Política de Privacidad visible")

                # 2. Cookies (30 puntos)
                if "cookie" in text_content:
                    passed.append("Mención de Cookies detectada")
                    score += 30
                else:
                    failed.append("No se detectó aviso o mención de Cookies")

                # 3. Datos Personales (30 puntos)
                if "datos personales" in text_content:
                    passed.append("Mención de tratamiento de datos personales")
                    score += 30
                else:
                    failed.append("No se detectó mención a datos personales")

                results = {
                    "url": url,
                    "score": score,
                    "passed": passed,
                    "failed": failed,
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