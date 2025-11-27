import json
from app import create_app


def test_cards_endpoint():
    app = create_app()
    client = app.test_client()

    resp = client.post('/api/cards', json={'reading': 'three', 'crystal': 'amethyst'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['reading'] == 'three'
    assert len(data['cards']) == 3


def test_chat_endpoint():
    app = create_app()
    client = app.test_client()

    resp = client.post('/api/chat', json={'message': 'Tell me about my love life', 'crystal': 'rose'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'reply' in data
