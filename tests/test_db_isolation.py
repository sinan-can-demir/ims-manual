# tests/test_db_isolation.py

def test_isolation(client):
    # create product
    response = client.post("/api/products", json={
        "name": "Test",
        "sku": "ABC123"
    })
    assert response.status_code == 201


def test_isolation_again(client):
    # should NOT conflict
    response = client.post("/api/products", json={
        "name": "Test",
        "sku": "ABC123"
    })
    assert response.status_code == 201