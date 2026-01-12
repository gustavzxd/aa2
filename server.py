from flask import Flask, request, session, redirect, jsonify, send_from_directory
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__, static_folder='static', template_folder='pages')
app.secret_key = 'supersecretkey'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Dados e arquivos
occurrences = []
next_id = 1
logs = []
LOG_FILE = 'logs.json'
OCORRENCIAS_FILE = 'ocorrencias.json'

# --- Funções auxiliares ---
def carregar_ocorrencias():
    global occurrences, next_id
    if os.path.exists(OCORRENCIAS_FILE):
        try:
            with open(OCORRENCIAS_FILE, 'r', encoding='utf-8') as f:
                occurrences = json.load(f)
            if occurrences:
                next_id = max(o['id'] for o in occurrences) + 1
        except json.JSONDecodeError:
            occurrences = []
    else:
        occurrences = []

def salvar_ocorrencias():
    with open(OCORRENCIAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(occurrences, f, ensure_ascii=False, indent=2)

# --- Logs persistentes ---
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

def add_log(user, action, raw_data=None):
    now = datetime.now()
    entry = {
        'data': now.strftime("%Y-%m-%d"),
        'hora': now.strftime("%H:%M:%S"),
        'usuario': user,
        'acao': action,
        'raw': json.dumps(raw_data, indent=2, ensure_ascii=False) if raw_data else "{}"
    }
    logs.append(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# --- Segurança e autenticação ---
@app.before_request
def check_auth():
    # Permitir acesso a arquivos estáticos, login e raiz
    if request.endpoint in ['static', 'login_page', 'login_action', 'root']:
        return None
    if not session.get('user'):
        return redirect('/login')
    return None

@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    csp = "default-src 'self' https://unpkg.com https://*.openstreetmap.org; "
    csp += "style-src 'self' 'unsafe-inline' https://unpkg.com; "
    csp += "script-src 'self' 'unsafe-inline' https://unpkg.com; "
    csp += ("img-src 'self' data: https://unpkg.com https://*.openstreetmap.org "
            "https://*.tile.openstreetmap.org https://raw.githubusercontent.com; ")
    csp += "font-src 'self' data:;"
    response.headers['Content-Security-Policy'] = csp
    return response

# --- Login ---
@app.route('/login', methods=['GET'])
def login_page():
    if session.get('user'):
        return redirect('/login')
    return send_from_directory('pages', 'login.html')

@app.route('/login', methods=['POST'])
def login_action():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if username == 'gustavo' and password == 'gotoso':
        session['user'] = username
        add_log(username, 'Login Realizado', {'ip': request.remote_addr})
        return jsonify({'ok': True})
    else:
        return jsonify({'ok': False, 'error': 'Credenciais inválidas'}), 401

@app.route('/logout')
def logout():
    user = session.get('user')
    if user:
        add_log(user, 'Logout Realizado')
    session.clear()
    return redirect('/login')

# --- Rotas principais ---
@app.route('/')
def root():
    if not session.get('user'):
        return redirect('/login')
    return redirect('/index')

@app.route('/index')
def index():
    return send_from_directory('pages', 'index.html')

@app.route('/mapa')
def mapa():
    return send_from_directory('pages', 'mapa.html')

@app.route('/lista')
def lista():
    return send_from_directory('pages', 'lista.html')

@app.route('/logs')
def logs_page():
    return send_from_directory('pages', 'logs.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# --- API ---
@app.route('/ocorrencias', methods=['GET'])
def get_ocorrencias():
    if not session.get('user'):
        return jsonify({'error': 'Não autorizado'}), 401
    return jsonify(occurrences)

@app.route('/registrar_ocorrencia', methods=['POST'])
def registrar_ocorrencia():
    if not session.get('user'):
        return jsonify({'error': 'Não autorizado'}), 401

    global next_id
    data = request.get_json() or {}
    
    try:
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'error': 'Coordenadas inválidas'}), 400

    entry = {
        'id': next_id,
        'data': datetime.now().strftime("%Y-%m-%d"),
        'hora': datetime.now().strftime("%H:%M:%S"),
        'tipo': data.get('tipo', 'Outros'),
        'prioridade': data.get('prioridade', 'Baixa'),
        'endereco': data.get('endereco', ''),
        'lat': lat,
        'lon': lon
    }
    occurrences.append(entry)
    salvar_ocorrencias()
    add_log(session['user'], f'Nova Ocorrência #{next_id}', raw_data=entry)
    next_id += 1
    return jsonify({'ok': True, 'id': next_id - 1})

@app.route('/excluir_ocorrencia', methods=['POST'])
def excluir_ocorrencia():
    if not session.get('user'):
        return jsonify({'error': 'Não autorizado'}), 401

    data = request.get_json() or {}
    occ_id = data.get('id')

    if not occ_id:
        return jsonify({'ok': False, 'error': 'ID não fornecido'}), 400

    global occurrences
    item_deleted = next((item for item in occurrences if item['id'] == occ_id), None)
    occurrences = [occ for occ in occurrences if occ['id'] != occ_id]

    if item_deleted:
        salvar_ocorrencias()
        add_log(session['user'], f'Excluiu Ocorrência #{occ_id}', raw_data=item_deleted)
        return jsonify({'ok': True})
    else:
        return jsonify({'ok': False, 'error': 'Ocorrência não encontrada'}), 404

@app.route('/logs_data', methods=['GET'])
def get_logs():
    if not session.get('user'):
        return jsonify({'error': 'Não autorizado'}), 401
    entries = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    else:
        entries = logs
    return jsonify(entries)

@app.errorhandler(Exception)
def handle_exception(e):
    user = session.get('user') or 'Desconhecido'
    add_log(user, 'Exceção Não Tratada', {'error': str(e)})
    return jsonify({'error': 'Internal Server Error'}), 500

# --- Inicialização ---
if __name__ == '__main__':
    os.makedirs('pages', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)

    carregar_ocorrencias()

    print("Servidor rodando em http://localhost:8000")
    print("Use Ctrl+C para parar o servidor")
    app.run(host='0.0.0.0', port=8000, debug=False)
