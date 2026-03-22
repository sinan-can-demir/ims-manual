from .utils import create_product


def test_sale_negative_quantity_fails(client):
    product = create_product(client)

    response = client.post("/api/inventory/events", json={
        "product_id": product["id"],
        "event_type": "SALE",
        "quantity": -5,
        "event_id": "evt-neg-sale"
    })

    assert response.status_code == 400


def test_purchase_negative_quantity_fails(client):
    product = create_product(client)

    response = client.post("/api/inventory/events", json={
        "product_id": product["id"],
        "event_type": "PURCHASE",
        "quantity": -3,
        "event_id": "evt-neg-purchase"
    })

    assert response.status_code == 400

def test_adjustment_negative_allowed(client):
    product = create_product(client)

    response = client.post("/api/inventory/events", json={
        "product_id": product["id"],
        "event_type": "ADJUSTMENT",
        "quantity": -10,
        "event_id": "evt-adjust-neg"
    })

    assert response.status_code == 201