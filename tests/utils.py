import uuid

def create_product(client, name="Item"):
    response = client.post(
        "/api/products",
        json={
            "name": name,
            "sku": f"sku-{uuid.uuid4()}"
        }
    )

    # Ensure product creation was successful
    # and status code is 201 (Created)
    assert response.status_code == 201, response.json()

    return response.json()