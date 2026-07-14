from .utils import create_product


def test_idempotent_event(client):

    product = create_product(client)
    product_id = product["id"]

    payload = {
        "product_id": product_id,
        "event_type": "PURCHASE",
        "quantity": 50,
        "event_id": "same-event",
    }

    # First request
    r1 = client.post("/api/inventory/events", json=payload)
    assert r1.status_code == 201

    # Duplicate request — same event_id, must return 201 without double-counting
    r2 = client.post("/api/inventory/events", json=payload)
    assert r2.status_code == 201

    # Inventory should still be 50 (not 100)
    response = client.get(f"/api/inventory/{product_id}")

    assert response.json()["quantity"] == 50
