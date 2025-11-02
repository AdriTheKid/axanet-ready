# app.py
from __future__ import annotations
from flask import Flask, jsonify, request
import json
import os
import threading
from typing import List, Dict, Any

app = Flask(__name__)

# --- Persistencia JSON ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "clients.json")

_lock = threading.Lock()


def _normalize_to_list(data: Any) -> List[Dict[str, Any]]:
    """Devuelve siempre una lista de diccionarios."""
    if isinstance(data, list):
        # Solo deja dicts bien formados
        return [x for x in data if isinstance(x, dict)]
    # Si es un dict suelto o cualquier otra cosa, lo tratamos como base vacía
    return []


def _safe_read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load() -> List[Dict[str, Any]]:
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        return []
    with _lock:
        try:
            data = _safe_read_json(DB_PATH)
        except (json.JSONDecodeError, OSError):
            return []
    return _normalize_to_list(data)


def _save(items: List[Dict[str, Any]]) -> None:
    with _lock:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)


def _next_id(items: List[Dict[str, Any]]) -> int:
    # Considera solo dicts con clave id numérica
    ids = [int(c["id"]) for c in items if isinstance(c, dict) and isinstance(c.get("id", 0), (int, float))]
    return (max(ids, default=0) + 1)


def _get_in(data: Dict[str, Any], *keys: str, default=None):
    """Obtén el primer key presente en data (útil para español/inglés)."""
    for k in keys:
        if k in data and data[k] not in (None, ""):
            return data[k]
    return default


# ------------------ Rutas ------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "message": "Axanet Client Manager running!"})


# Aliases: /clientes y /clients
@app.route("/clientes", methods=["GET"])
@app.route("/clients", methods=["GET"])
def list_clients():
    return jsonify(_load())


@app.route("/clientes/<int:cid>", methods=["GET"])
@app.route("/clients/<int:cid>", methods=["GET"])
def get_client(cid: int):
    items = _load()
    for c in items:
        if c.get("id") == cid:
            return jsonify(c)
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route("/clientes", methods=["POST"])
@app.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json(silent=True) or {}
    nombre = _get_in(data, "nombre", "name")
    servicio = _get_in(data, "servicio", "service")
    correo = _get_in(data, "correo", "email")
    extra = data.get("extra") or data.get("data") or {}

    if not nombre or not servicio:
        return jsonify({"error": "Campos requeridos: nombre/name y servicio/service"}), 400

    items = _load()
    new = {
        "id": _next_id(items),
        "nombre": nombre,
        "correo": correo,
        "servicio": servicio,
        "extra": extra,
    }
    items.append(new)
    _save(items)
    return jsonify({"mensaje": "Cliente agregado", "cliente": new}), 201


@app.route("/clientes/<int:cid>", methods=["PUT", "PATCH"])
@app.route("/clients/<int:cid>", methods=["PUT", "PATCH"])
def update_client(cid: int):
    data = request.get_json(silent=True) or {}
    items = _load()
    for c in items:
        if c.get("id") == cid:
            v = _get_in(data, "nombre", "name")
            if v is not None:
                c["nombre"] = v
            v = _get_in(data, "servicio", "service")
            if v is not None:
                c["servicio"] = v
            v = _get_in(data, "correo", "email")
            if v is not None:
                c["correo"] = v
            if "extra" in data or "data" in data:
                c["extra"] = data.get("extra") or data.get("data") or {}
            _save(items)
            return jsonify({"mensaje": "Cliente actualizado", "cliente": c})
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route("/clientes/<int:cid>", methods=["DELETE"])
@app.route("/clients/<int:cid>", methods=["DELETE"])
def delete_client(cid: int):
    items = _load()
    new_items = [c for c in items if c.get("id") != cid]
    if len(new_items) == len(items):
        return jsonify({"error": "Cliente no encontrado"}), 404
    _save(new_items)
    return jsonify({"mensaje": "Cliente eliminado", "id": cid})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
