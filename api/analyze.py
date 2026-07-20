from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
import re

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
                self._send_json(400, {"error": "Debes ingresar una URL"})
                return

            if not url.startswith('http'):
                url = 'https://' + url

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8'
            }
            
            response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            
            if response.status_code in [403, 401, 429]:
                self._send_json(200, {
                    "url": url,
                    "score": 0,
                    "passed": [],
                    "failed": ["El sitio bloqueó el análisis automático (protección anti-bot). Se requiere revisión manual."],
                    "title": "Acceso restringido"
                })
                return
                
            if response.status_code != 200:
                self._send_json(200, {
                    "url": url,
                    "score": 0,
                    "passed": [],
                    "failed": ["El sitio no respondió correctamente (Código: " + str(response.status_code) + ")"],
                    "title": "Sitio no accesible"
                })
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            # Obtener texto y normalizar (minúsculas, sin tildes para búsqueda flexible)
            text_content = self._normalize_text(soup.get_text())
            title = soup.title.string.strip() if soup.title else 'Sin título'

            passed = []
            failed = []
            score = 0

            # 1. Política de Privacidad (40 puntos)
            if self._has_keyword(text_content, ["politica de privacidad", "aviso de privacidad", "privacy policy", "privacidad"]):
                passed.append("Aviso de Política de Privacidad detectado")
                score += 40
            else:
                failed.append("No se detectó una Política de Privacidad visible")

            # 2. Cookies (30 puntos)
            if self._has_keyword(text_content, ["politica de cookies", "uso de cookies", "cookies", "cookie policy"]):
                passed.append("Mención de Cookies detectada")
                score += 30
            else:
                failed.append("No se detectó aviso o mención de Cookies")

            # 3. Datos Personales (30 puntos)
            if self._has_keyword(text_content, ["datos personales", "proteccion de datos", "personal data", "ley 21.719", "gdpr"]):
                passed.append("Mención de tratamiento de datos personales")
                score += 30
            else:
                failed.append("No se detectó mención a datos personales o protección de datos")

            self._send_json(200, {
                "url": url,
                "score": score,
                "passed": passed,
                "failed": failed,
                "title": title
            })

        except requests.exceptions.Timeout:
            self._send_json(200, {"url": url, "score": 0, "passed": [], "failed": ["El sitio tardó demasiado en responder (Timeout)."], "title": "Timeout"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_GET(self):
        self._send_json(405, {"error": "Método no permitido"})

    def _normalize_text(self, text):
        # Convierte a minúsculas y elimina tildes para búsquedas más flexibles
        text = text.lower()
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        return text

    def _has_keyword(self, text, keywords):
        return any(keyword in text for keyword in keywords)

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))