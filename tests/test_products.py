def test_create_product(client):
    response = client.post(
        "/api/products",
        json={
            "name": "Test Product",
            "sku": "test-sku-1"
        }
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.json())

    assert response.status_code == 200