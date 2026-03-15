#!/bin/bash

set -euo pipefail

BASE="http://localhost:8000"

echo "Starting containers..."

docker compose down
docker compose up --build -d

echo "Waiting for API to become ready..."

for i in {1..30}; do
    if curl -s "$BASE/docs" > /dev/null; then
        echo "API is ready"
        break
    fi

    if [ "$i" -eq 30 ]; then
        echo "FAIL: API did not become ready in time"
        exit 1
    fi

    sleep 1
done


############################################
# Test 1 — Create Product
############################################

echo "Testing POST /api/products"

SKU="test-sku-$(date +%s)"

response=$(curl -s -w "%{http_code}" -X POST "$BASE/api/products" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"test-product\",\"sku\":\"$SKU\"}")

body="${response::-3}"
status="${response: -3}"

echo "Status: $status"
echo "Body: $body"

if [[ "$status" != "200" && "$status" != "201" ]]; then
    echo "FAIL: Create product"
    exit 1
fi

product_id=$(echo "$body" | jq -r '.id')

if [[ -z "$product_id" || "$product_id" == "null" ]]; then
    echo "FAIL: Could not extract product id"
    exit 1
fi

echo "PASS: Product created with id $product_id"


############################################
# Test 2 — Purchase Inventory
############################################

echo "Testing POST /api/inventory/events (PURCHASE)"

purchase_response=$(curl -s -w "%{http_code}" -X POST "$BASE/api/inventory/events" \
  -H "Content-Type: application/json" \
  -d "{\"product_id\":$product_id,\"event_type\":\"PURCHASE\",\"quantity\":50}")

purchase_body="${purchase_response::-3}"
purchase_status="${purchase_response: -3}"

echo "Status: $purchase_status"
echo "Body: $purchase_body"

if [[ "$purchase_status" != "201" && "$purchase_status" != "200" ]]; then
    echo "FAIL: Purchase event failed"
    exit 1
fi

echo "PASS: Purchase event recorded"


############################################
# Test 3 — Verify Inventory = 50
############################################

echo "Testing GET /api/inventory/$product_id"

inventory_response=$(curl -s -w "%{http_code}" -X GET "$BASE/api/inventory/$product_id")

inventory_body="${inventory_response::-3}"
inventory_status="${inventory_response: -3}"

echo "Status: $inventory_status"
echo "Body: $inventory_body"

if [[ "$inventory_status" != "200" ]]; then
    echo "FAIL: Inventory lookup failed"
    exit 1
fi

quantity=$(echo "$inventory_body" | jq -r '.inventory')

if [[ -z "$quantity" || "$quantity" == "null" ]]; then
    echo "FAIL: Could not parse inventory value"
    exit 1
fi

if [[ "$quantity" != "50" ]]; then
    echo "FAIL: Expected inventory 50, got $quantity"
    exit 1
fi

echo "PASS: Inventory correctly updated to 50"


############################################
# Test 4 — Sale Event
############################################

echo "Testing POST /api/inventory/events (SALE)"

sale_response=$(curl -s -w "%{http_code}" -X POST "$BASE/api/inventory/events" \
  -H "Content-Type: application/json" \
  -d "{\"product_id\":$product_id,\"event_type\":\"SALE\",\"quantity\":10}")

sale_body="${sale_response::-3}"
sale_status="${sale_response: -3}"

echo "Status: $sale_status"
echo "Body: $sale_body"

if [[ "$sale_status" != "201" && "$sale_status" != "200" ]]; then
    echo "FAIL: Sale event failed"
    exit 1
fi

echo "PASS: Sale event recorded"


############################################
# Test 5 — Verify Inventory = 40
############################################

echo "Testing GET /api/inventory/$product_id after sale"

inventory_response=$(curl -s -w "%{http_code}" -X GET "$BASE/api/inventory/$product_id")

inventory_body="${inventory_response::-3}"
inventory_status="${inventory_response: -3}"

echo "Status: $inventory_status"
echo "Body: $inventory_body"

if [[ "$inventory_status" != "200" ]]; then
    echo "FAIL: Inventory lookup after sale failed"
    exit 1
fi

quantity=$(echo "$inventory_body" | jq -r '.inventory')

if [[ -z "$quantity" || "$quantity" == "null" ]]; then
    echo "FAIL: Could not parse inventory value after sale"
    exit 1
fi

if [[ "$quantity" != "40" ]]; then
    echo "FAIL: Expected inventory 40, got $quantity"
    exit 1
fi

echo "PASS: Inventory correctly updated to 40"


############################################
# Test 6 — Oversell Protection
############################################

echo "Testing oversell protection"

oversell_response=$(curl -s -w "%{http_code}" -X POST "$BASE/api/inventory/events" \
  -H "Content-Type: application/json" \
  -d "{\"product_id\":$product_id,\"event_type\":\"SALE\",\"quantity\":100}")

oversell_body="${oversell_response::-3}"
oversell_status="${oversell_response: -3}"

echo "Status: $oversell_status"
echo "Body: $oversell_body"

if [[ "$oversell_status" != "400" ]]; then
    echo "FAIL: Oversell protection not triggered"
    exit 1
fi

echo "PASS: Oversell correctly rejected"


############################################

echo ""
echo "All system tests passed successfully"