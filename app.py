from __future__ import annotations

import json
import os
import threading
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from flask import Flask
from flask import jsonify
from flask import request


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "clients.json")

_lock = threading.Lock()


def _normalize_to_list(data: Any) -> List[Dict[str, Any]]:
    """Devuelve siempre una lista de diccionarios."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
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
    ids = [
        int(c["id"])
        for c in items
        if isinstance(c, dict) and isinstance(c.get("id", 0), (int, float))
    ]
    return max(ids, default=0) + 1


def _get_in(data: Dict[str, Any], *keys: str, default=None):
    """Obtén el primer key presente (útil para español/inglés)."""
    for k in keys:
        if k in data and data[k] not in (None, ""):
            return data[k]
    return default


def _find_by_id(items: List[Dict[str, Any]], cid: int) -> Optional[Dict[str, Any]]:
    for c in items:
        if c.get("id") == cid:
            return c
    return None


def _find_by_name(items: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    target = name.strip().lower()
    for c in items:
        n = (c.get("nombre") or c.get("name") or "").strip().lower()
        if n == target:
            return c
    return None


def _find_by_key(items: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    try:
        return _find_by_id(items, int(key))
    except (ValueError, TypeError):
        return _find_by_name(items, key)


@app.get("/")
def home():
    return jsonify({"ok": True, "message": "Axanet Client Manager running!"})


@app.get("/clientes")
@app.get("/clients")
def list_clients():
    return jsonify(_load())


@app.get("/clientes/<path:key>")
@app.get("/clients/<path:key>")
def get_client_any(key: str):
    items = _load()
    c = _find_by_key(items, key)
    if c:
        return jsonify(c)
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.post("/clientes")
@app.post("/clients")
def create_client():
    data = request.get_json(silent=True) or {}

    nombre = _get_in(data, "nombre", "name")
    servicio = _get_in(data, "servicio", "service")
    correo = _get_in(data, "correo", "email")
    extra = data.get("extra") or data.get("data") or {}

    if not nombre or not servicio:
        return (
            jsonify({"error": "Campos requeridos: nombre/name y servicio/service"}),
            400,
        )

    items = _load()
    new = {
        "id": _next_id(items),
        "nombre": nombre,
        "name": nombre,
        "correo": correo,
        "servicio": servicio,
        "service": servicio,
        "extra": extra,
    }
    items.append(new)
    _save(items)
    return jsonify({"mensaje": "Cliente agregado", "cliente": new}), 201


@app.put("/clientes/<path:key>")
@app.put("/clients/<path:key>")
@app.patch("/clientes/<path:key>")
@app.patch("/clients/<path:key>")
def update_client_any(key: str):
    data = request.get_json(silent=True) or {}
    items = _load()
    c = _find_by_key(items, key)
    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404

    v = _get_in(data, "nombre", "name")
    if v is not None:
        c["nombre"] = v
        c["name"] = v

    v = _get_in(data, "servicio", "service")
    if v is not None:
        c["servicio"] = v
        c["service"] = v

    v = _get_in(data, "correo", "email")
    if v is not None:
        c["correo"] = v

    if "extra" in data or "data" in data:
        c["extra"] = data.get("extra") or data.get("data") or {}

    _save(items)
    return jsonify({"mensaje": "Cliente actualizado", "cliente": c})


@app.delete("/clientes/<path:key>")
@app.delete("/clients/<path:key>")
def delete_client_any(key: str):
    items = _load()
    c = _find_by_key(items, key)
    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404
    new_items = [x for x in items if x is not c]
    _save(new_items)
    return jsonify(
        {
            "mensaje": "Cliente eliminado",
            "id": c.get("id"),
            "name": c.get("nombre") or c.get("name"),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
