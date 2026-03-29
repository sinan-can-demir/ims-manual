# tests/test_pagination.py

from .utils import create_product, purchase

def test_limit(client, db):
    product = create_product(client)
    pid = product["id"]
    purchase(client, pid, 10)
    purchase(client, pid, 10)
    purchase(client, pid, 10)

    res = client.get(f"/api/inventory/events/{pid}?limit=1")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_offset(client, db):
    product = create_product(client)
    pid = product["id"]
    
    e1 = purchase(client, pid, 10)
    purchase(client, pid, 10)
    purchase(client, pid, 10)

    res = client.get(f"/api/inventory/events/{pid}?offset=1")
    assert res.status_code == 200
    data = res.json()

    assert len(data) == 2
    # first event in response should be the second one created
    assert data[0]["id"] != e1["id"]