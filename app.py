# app.py
from __future__ import annotations
from flask import Flask, jsonify, request
import json
import os
import threading
from typing import List, Dict, Any

app = Flask(__name__)

# --- Persistencia en archivo JSON ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "clients.json")

_lock = threading.Lock()


def _load() -> List[Dict[str, Any]]:
    if not os.path.exists(DB_PATH):
        return []
    with _lock:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []


def _save(items: List[Dict[str, Any]]) -> None:
    with _lock:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)


def _next_id(items: List[Dict[str, Any]]) -> int:
    return (max((c.get("id", 0) for c in items), default=0) + 1)


# --- Rutas ---
@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "message": "Axanet Client Manager running!"})


@app.route("/clientes", methods=["GET"])
def listar_clientes():
    clientes = _load()
    return jsonify(clientes)


@app.route("/clientes/<int:cid>", methods=["GET"])
def obtener_cliente(cid: int):
    clientes = _load()
    for c in clientes:
        if c.get("id") == cid:
            return jsonify(c)
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route("/clientes", methods=["POST"])
def crear_cliente():
    data = request.get_json(silent=True) or {}
    requerido = ("nombre", "servicio")
    if any(not data.get(k) for k in requerido):
        return jsonify({"error": "Campos requeridos: nombre, servicio"}), 400

    clientes = _load()
    new = {
        "id": _next_id(clientes),
        "nombre": data.get("nombre"),
        "correo": data.get("correo"),
        "servicio": data.get("servicio"),
        "extra": data.get("extra", {}),
    }
    clientes.append(new)
    _save(clientes)
    return jsonify({"mensaje": "Cliente agregado", "cliente": new}), 201


@app.route("/clientes/<int:cid>", methods=["PUT", "PATCH"])
def actualizar_cliente(cid: int):
    data = request.get_json(silent=True) or {}
    clientes = _load()
    for c in clientes:
        if c.get("id") == cid:
            # Actualiza solo campos presentes
            for k in ("nombre", "correo", "servicio", "extra"):
                if k in data:
                    c[k] = data[k]
            _save(clientes)
            return jsonify({"mensaje": "Cliente actualizado", "cliente": c})
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route("/clientes/<int:cid>", methods=["DELETE"])
def borrar_cliente(cid: int):
    clientes = _load()
    nuevo = [c for c in clientes if c.get("id") != cid]
    if len(nuevo) == len(clientes):
        return jsonify({"error": "Cliente no encontrado"}), 404
    _save(nuevo)
    return jsonify({"mensaje": "Cliente eliminado", "id": cid})


# Necesario si lo corres directamente (debug/local). En EC2 usamos Gunicorn.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
