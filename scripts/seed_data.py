# scripts/seed_data.py
#
# Generates realistic inventory events spread across 30 days for 3 products.
# Calls the live API so all validation, projection, and idempotency logic applies.
#
# Usage:
#   python scripts/seed_data.py
#
# Requirements:
#   - Docker stack must be running (make up)
#   - API must be healthy at http://localhost:8000

import random
from datetime import date, timedelta

import requests

BASE = "http://localhost:8000"

# -------------------------------------------------------------------
# Products to seed
# -------------------------------------------------------------------
PRODUCTS = [
    {"name": "Widget A", "sku": "WGT-001"},
    {"name": "Widget B", "sku": "WGT-002"},
    {"name": "Widget C", "sku": "WGT-003"},
]

# -------------------------------------------------------------------
# Demand profiles — units sold per day follow these patterns
# Each tuple is (mean_daily_sales, std_dev)
# std_dev adds realistic noise so the model has something to learn
# -------------------------------------------------------------------
DEMAND_PROFILES = {
    "WGT-001": {"mean": 15, "std": 4},  # steady seller
    "WGT-002": {"mean": 5, "std": 2},  # slow mover
    "WGT-003": {"mean": 30, "std": 8},  # high volume
}

START_DATE = date(2026, 3, 1)
DAYS = 30


def post(endpoint: str, payload: dict) -> requests.Response:
    return requests.post(f"{BASE}{endpoint}", json=payload)


def create_products() -> dict[str, int]:
    """Create products and return a mapping of SKU -> product_id."""
    product_ids = {}

    for product in PRODUCTS:
        response = post("/api/products", product)

        if response.status_code == 201:
            pid = response.json()["id"]
            product_ids[product["sku"]] = pid
            print(f"  ✓ Created {product['name']} (id={pid})")

        elif response.status_code == 409:
            # Already exists — this is fine, seed is idempotent
            # We need to look up the id a different way
            # For simplicity, warn and skip — re-run after make reset if needed
            print(
                f"  ⚠ {product['name']} already exists (SKU conflict). "
                f"Run make reset first for a clean seed."
            )

        else:
            print(f"  ✗ Failed to create {product['name']}: {response.text}")

    return product_ids


def seed_events(product_ids: dict[str, int]) -> None:
    """
    For each product, generate 30 days of realistic events:
    - Initial PURCHASE on day 1 (bulk restock)
    - Daily SALE events with realistic demand noise
    - Occasional RETURN events (roughly 1 in 7 days)
    - Mid-period PURCHASE restock when stock gets low
    """
    for sku, product_id in product_ids.items():
        profile = DEMAND_PROFILES[sku]
        mean = profile["mean"]
        std = profile["std"]

        print(f"\n  Seeding {sku} (product_id={product_id})...")

        # --- Initial bulk purchase on day 1 ---
        initial_stock = mean * 20  # ~20 days of stock to start
        post(
            "/api/inventory/events",
            {
                "product_id": product_id,
                "event_type": "PURCHASE",
                "quantity": initial_stock,
                "event_id": f"seed-purchase-initial-{sku}",
            },
        )
        print(f"    Day 0: PURCHASE {initial_stock} units (initial stock)")

        for day_offset in range(DAYS):
            current_date = START_DATE + timedelta(days=day_offset)
            day_label = current_date.isoformat()

            # --- Daily sale ---
            # clip at 1 to avoid zero or negative quantities
            daily_demand = max(1, int(random.gauss(mean, std)))

            sale_response = post(
                "/api/inventory/events",
                {
                    "product_id": product_id,
                    "event_type": "SALE",
                    "quantity": daily_demand,
                    "event_id": f"seed-sale-{sku}-{day_label}",
                },
            )

            if sale_response.status_code == 201:
                print(f"    {day_label}: SALE {daily_demand} units")
            elif sale_response.status_code == 400:
                # Oversell protection triggered — stock ran out
                # Restock before continuing
                restock_qty = mean * 10
                post(
                    "/api/inventory/events",
                    {
                        "product_id": product_id,
                        "event_type": "PURCHASE",
                        "quantity": restock_qty,
                        "event_id": f"seed-restock-{sku}-{day_label}",
                    },
                )
                print(f"    {day_label}: ⚠ Oversell blocked → PURCHASE {restock_qty} (emergency)")

            # --- Occasional return (roughly 1 in 7 days) ---
            if random.random() < 0.14:
                return_qty = random.randint(1, 3)
                post(
                    "/api/inventory/events",
                    {
                        "product_id": product_id,
                        "event_type": "RETURN",
                        "quantity": return_qty,
                        "event_id": f"seed-return-{sku}-{day_label}",
                    },
                )
                print(f"    {day_label}: RETURN {return_qty} units")

            # --- Mid-period restock (around day 15) ---
            if day_offset == 14:
                restock_qty = mean * 15
                post(
                    "/api/inventory/events",
                    {
                        "product_id": product_id,
                        "event_type": "PURCHASE",
                        "quantity": restock_qty,
                        "event_id": f"seed-restock-mid-{sku}",
                    },
                )
                print(f"    {day_label}: PURCHASE {restock_qty} units (mid-period restock)")


def main() -> None:
    print("=" * 55)
    print("IMS Seed Script — 30 days of realistic inventory data")
    print("=" * 55)

    # 1. Health check
    try:
        requests.get(f"{BASE}/docs", timeout=3)
    except requests.ConnectionError:
        print("\n✗ API is not reachable at http://localhost:8000")
        print("  Run: make up")
        return

    # 2. Create products
    print("\n[1/2] Creating products...")
    product_ids = create_products()

    if not product_ids:
        print("\n✗ No products created. Exiting.")
        return

    # 3. Seed events
    print("\n[2/2] Seeding inventory events...")
    seed_events(product_ids)

    # 4. Summary
    print("\n" + "=" * 55)
    print("✓ Seeding complete.")
    print(f"  Products seeded : {len(product_ids)}")
    print(f"  Days of history : {DAYS}")
    print()
    print("Next steps:")
    print("  make export")
    print("  make dbt-run")
    print("  make features")
    print("  make train")
    print("=" * 55)


if __name__ == "__main__":
    main()
