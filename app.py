#Nombre: Tomás Olmos Vásquez
import re
from flask import Flask, request, abort, jsonify
from markupsafe import escape

app = Flask(__name__)

# Validación estricta: solo letras, números, espacios y guiones (máx. 50 caracteres)
NAME_PATTERN = re.compile(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ _-]{1,50}$')


@app.after_request
def add_security_headers(response):
    # Mitigación de alertas OWASP ZAP [10020, 10021, 10038, 10049, 10063, 90004]
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
        abort(400, description="Parámetro 'name' inválido.")

    safe_name = escape(raw_name)
    return f'Hello, {safe_name}!', 200


if __name__ == '__main__':
    # Nunca ejecutar con debug=True en producción
    app.run(host='127.0.0.1', port=5000, debug=False)