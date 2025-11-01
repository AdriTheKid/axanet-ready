# tests/test_app.py
from app import app


def test_health():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json()['ok'] is True


def test_crud():
    client = app.test_client()

    # Crear cliente
    response = client.post(
        '/clients',
        json={'name': 'TestUser', 'service': 'Internet', 'data': {'plan': 'Pro'}}
    )
    assert response.status_code in (200, 201)

    # Obtener cliente
    response = client.get('/clients/TestUser')
    assert response.status_code == 200
    assert response.get_json()['name'] == 'TestUser'

    # Actualizar cliente
    response = client.put(
        '/clients/TestUser',
        json={'data': {'plan': 'Premium'}}
    )
    assert response.status_code == 200
    assert response.get_json()['client']['data']['plan'] == 'Premium'

    # Borrar cliente
    response = client.delete('/clients/TestUser')
    assert response.status_code == 200
    assert response.get_json()['ok'] is True