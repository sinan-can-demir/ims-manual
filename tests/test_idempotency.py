from .utils import create_product

def test_idempotent_event(client):

    product = create_product(client)
    product_id = product["id"]

    payload = {
        "product_id": product_id,
        "event_type": "PURCHASE",
        "quantity": 50,
        "event_id": "same-event"
    }

    # First request
    client.post("/api/inventory/events", json=payload)

    # Duplicate request
    client.post("/api/inventory/events", json=payload)

    # Inventory should still be 50 (not 100)
    response = client.get(f"/api/inventory/{product_id}")

    assert response.json()["inventory"] == 50