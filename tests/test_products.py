def test_create_product(client):
    response = client.post("/api/products", json={"name": "Test Product", "sku": "test-sku-1"})

    assert response.status_code == 201


def test_duplicate_sku_returns_409(client):
    payload = {"name": "Test Product", "sku": "duplicate-sku"}

    # First creation
    response1 = client.post("/api/products", json=payload)
    assert response1.status_code == 201

    # Duplicate creation
    response2 = client.post("/api/products", json=payload)

    assert response2.status_code == 409
    assert "already exists" in response2.text
