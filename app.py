#Nombre: Tomás Olmos Vásquez
import re
import time
from collections import defaultdict
from flask import Flask, request, abort, jsonify, Response
from markupsafe import escape

app = Flask(__name__)

NAME_PATTERN = re.compile(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ _-]{1,50}$')

# Métricas en memoria para monitorización en tiempo real
REQUEST_COUNT = defaultdict(int)
SECURITY_BLOCKS = defaultdict(int)
REQUEST_LATENCY_SUM = 0.0
REQUEST_LATENCY_COUNT = 0


@app.before_request
def start_timer():
    request._start_time = time.time()


@app.after_request
def after_request_hooks(response):
    global REQUEST_LATENCY_SUM, REQUEST_LATENCY_COUNT

    # Registrar métricas (excluyendo el scraping de /metrics)
    if request.path != '/metrics':
        latency = time.time() - getattr(request, '_start_time', time.time())
        REQUEST_LATENCY_SUM += latency
        REQUEST_LATENCY_COUNT += 1
        REQUEST_COUNT[(request.method, request.path, str(response.status_code))] += 1

    # Cabeceras de seguridad HTTP
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
    )
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/')
def index():
    return jsonify({"status": "ok", "service": "SecureDev API"}), 200


@app.route('/hello')
def hello():
    raw_name = request.args.get('name', 'Guest')

    if not NAME_PATTERN.match(raw_name):
        SECURITY_BLOCKS['invalid_or_xss_payload'] += 1
        abort(400, description="Parámetro 'name' inválido.")

    safe_name = escape(raw_name)
    return f'Hello, {safe_name}!', 200


@app.route('/metrics')
def metrics():
    lines = [
        '# HELP securedev_http_requests_total Total de peticiones HTTP procesadas',
        '# TYPE securedev_http_requests_total counter',
    ]
    for (method, path, status), count in REQUEST_COUNT.items():
        lines.append(
            f'securedev_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
        )

    lines.extend([
        '# HELP securedev_security_blocks_total Intentos de entrada maliciosa bloqueados',
        '# TYPE securedev_security_blocks_total counter',
    ])
    for reason, count in SECURITY_BLOCKS.items():
        lines.append(f'securedev_security_blocks_total{{reason="{reason}"}} {count}')

    lines.extend([
        '# HELP securedev_http_request_duration_seconds_sum Suma de latencia HTTP',
        '# TYPE securedev_http_request_duration_seconds_sum counter',
        f'securedev_http_request_duration_seconds_sum {REQUEST_LATENCY_SUM:.6f}',
        '# HELP securedev_http_request_duration_seconds_count Conteo de latencia HTTP',
        '# TYPE securedev_http_request_duration_seconds_count counter',
        f'securedev_http_request_duration_seconds_count {REQUEST_LATENCY_COUNT}',
    ])
    return Response('\n'.join(lines) + '\n', mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)