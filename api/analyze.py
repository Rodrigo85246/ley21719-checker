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
                self._send_json(400, {"error": "Debes ingresar una URL"})
                return

            if not url.startswith('http'):
                url = 'https://' + url

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8'
            }
            
            response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            
            if response.status_code in [403, 401, 429]:
                self._send_json(200, {"url": url, "score": 0, "passed": [], "failed": [], "blocked": True, "title": "Acceso restringido"})
                return
                
            if response.status_code != 200:
                self._send_json(200, {"url": url, "score": 0, "passed": [], "failed": ["El sitio no respondió correctamente (Código: " + str(response.status_code) + ")"], "title": "Sitio no accesible"})
                return

            html_clean = response.text.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else 'Sin título'

            passed = []
            failed = []
            score = 0

            if any(kw in html_clean for kw in ["politica de privacidad", "aviso de privacidad", "privacy policy", "privacidad", "proteccion de datos", "terminos y condiciones", "terms of service"]):
                passed.append("Aviso de Privacidad / Términos detectado")
                score += 40
            else:
                failed.append("No se detectó Política de Privacidad o Términos de Servicio")

            if any(kw in html_clean for kw in ["politica de cookies", "uso de cookies", "cookies", "cookie policy", "consentimiento", "consent", "gdpr", "cmg"]):
                passed.append("Gestión o mención de Cookies detectada")
                score += 30
            else:
                failed.append("No se detectó aviso de Cookies o consentimiento")

            if any(kw in html_clean for kw in ["datos personales", "informacion personal", "personal data", "ley 21.719", "gdpr", "tratamiento de datos", "recopilacion de datos"]):
                passed.append("Mención de tratamiento de datos personales")
                score += 30
            else:
                failed.append("No se detectó mención explícita a datos personales")

            self._send_json(200, {"url": url, "score": score, "passed": passed, "failed": failed, "title": title})

        except requests.exceptions.ConnectionError:
            # Captura el "Connection refused" de Emol y otros WAFs
            self._send_json(200, {"url": url, "score": 0, "passed": [], "failed": [], "blocked": True, "title": "Sitio protegido por Firewall"})
        except requests.exceptions.Timeout:
            self._send_json(200, {"url": url, "score": 0, "passed": [], "failed": ["El sitio tardó demasiado en responder (Timeout)."], "title": "Timeout"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_GET(self):
        self._send_json(405, {"error": "Método no permitido"})

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))