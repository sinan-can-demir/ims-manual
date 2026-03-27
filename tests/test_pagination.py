# tests/test_pagination.py

import uuid
from .utils import create_product


def _purchase(client, product_id: int):
    response = client.post("/api/inventory/events", json={
        "product_id": product_id,
        "event_type": "PURCHASE",
        "quantity": 10,
        "event_id": f"evt-{uuid.uuid4()}",
    })
    assert response.status_code == 201
    return response.json()


def test_limit(client, db):
    product = create_product(client)
    pid = product["id"]

    _purchase(client, pid)
    _purchase(client, pid)
    _purchase(client, pid)

    res = client.get(f"/api/inventory/events/{pid}?limit=1")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_offset(client, db):
    product = create_product(client)
    pid = product["id"]

    e1 = _purchase(client, pid)
    _purchase(client, pid)
    _purchase(client, pid)

    res = client.get(f"/api/inventory/events/{pid}?offset=1")
    assert res.status_code == 200
    data = res.json()

    assert len(data) == 2
    # first event in response should be the second one created
    assert data[0]["id"] != e1["id"]