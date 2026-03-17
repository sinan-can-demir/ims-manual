import uuid

def create_product(client, name="Item"):
    response = client.post(
        "/api/products",
        json={
            "name": name,
            "sku": f"sku-{uuid.uuid4()}"
        }
    )

    assert response.status_code == 200, response.json()

    return response.json()