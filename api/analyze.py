import json
import requests
from bs4 import BeautifulSoup

def handler(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Accept',
    }

    if request.method == 'OPTIONS':
        return {'statusCode': 204, 'headers': headers, 'body': ''}

    if request.method == 'POST':
        try:
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            
            data = json.loads(body) if body else {}
            url = data.get('url')

            if not url:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "Debes ingresar una URL"})}

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

            return {'statusCode': 200, 'headers': headers, 'body': json.dumps(results)}

        except Exception as e:
            return {'statusCode': 500, 'headers': headers, 'body': json.dumps({"error": str(e)})}

    return {'statusCode': 405, 'headers': headers, 'body': json.dumps({"error": "Método no permitido"})}