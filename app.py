from flask import Flask, jsonify, request
import os, json, threading
from datetime import datetime

app = Flask(__name__)
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'clients.json')
_LOCK = threading.Lock()

def _load():
    if not os.path.exists(DATA_PATH):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump({'_meta': {'version': 1}}, f)
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save(data):
    tmp = DATA_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_PATH)

@app.get('/')
def health():
    return jsonify({'ok': True, 'ts': datetime.utcnow().isoformat()})

@app.get('/clients')
def list_clients():
    with _LOCK:
        data = _load()
    clients = [k for k in data.keys() if k != '_meta']
    return jsonify({'count': len(clients), 'clients': clients})

@app.post('/clients')
def create_client():
    body = request.get_json(force=True, silent=True) or {}
    name = body.get('name')
    service = body.get('service', 'unspecified')
    extra = body.get('data', {})
    if not name:
        return jsonify({'error': "Missing 'name'"}), 400
    with _LOCK:
        data = _load()
        if name in data:
            return jsonify({'error': 'Client already exists'}), 409
        data[name] = {'name': name, 'service': service, 'history': [{'action':'create','service':service,'ts': datetime.utcnow().isoformat()}], 'data': extra}
        _save(data)
    return jsonify({'ok': True, 'client': data[name]}), 201

@app.get('/clients/<name>')
def get_client(name):
    with _LOCK:
        data = _load()
        if name not in data:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(data[name])

@app.put('/clients/<name>')
def update_client(name):
    body = request.get_json(force=True, silent=True) or {}
    patch = body.get('data', {})
    service = body.get('service')
    with _LOCK:
        data = _load()
        if name not in data:
            return jsonify({'error': 'Not found'}), 404
        if patch:
            data[name]['data'].update(patch)
        if service:
            data[name]['service'] = service
        data[name]['history'].append({'action':'update','service': service or data[name]['service'],'ts': datetime.utcnow().isoformat()})
        _save(data)
    return jsonify({'ok': True, 'client': data[name]})

@app.delete('/clients/<name>')
def delete_client(name):
    with _LOCK:
        data = _load()
        if name not in data:
            return jsonify({'error': 'Not found'}), 404
        deleted = data.pop(name)
        _save(data)
    return jsonify({'ok': True, 'deleted': deleted})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
