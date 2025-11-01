from app import app

def test_health():
    c = app.test_client()
    r = c.get('/')
    assert r.status_code == 200
    assert r.get_json()['ok'] is True

def test_crud():
    c = app.test_client()
    r = c.post('/clients', json={'name':'T','service':'S','data':{}})
    assert r.status_code in (200,201)
    r = c.get('/clients/T')
    assert r.status_code == 200
    r = c.put('/clients/T', json={'data': {'x':1}})
    assert r.status_code == 200
    r = c.delete('/clients/T')
    assert r.status_code == 200
