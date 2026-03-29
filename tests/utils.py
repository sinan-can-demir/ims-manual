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

def purchase(client, product_id, quantity):
    event_id = f"evt-{uuid.uuid4()}"
    response = client.post("/api/inventory/events", json={
        "product_id": product_id,
        "event_type": "PURCHASE",
        "quantity": quantity,
        "event_id": event_id,
    })
    assert response.status_code == 201
    return response.json()