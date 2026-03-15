# Debug Notes

## 3/14/2026

### BUG #1

[x] sqlalchemy.exc.CompileError: PostgreSQL ENUM type requires a name.

- This is a very common SQLAlchemy + PostgreSQL Enum issue. PostgreSQL requires names for Enums but SQLAlchemy doesn't create them unless you make it.
    
- To solve this we added this to `app/models/inventory_event.py`
    
```py
    event_type = Column(
    Enum(EventType, name="event_type_enum"),
    nullable=False)
```

This solves the problm, docker composes up successfully.

## 3/15/2026

### BUG #1

[?] `test_scripts/test_sc.sh` had a bug that couses an internal server errpr

- the error points the product creation:

```bash
Waiting for API to start...
Testing POST /api/products
Status: 500
Body: Internal Server Error
FAIL: Create product
```

- The very first thing to do is to run:

```bash 
docker logs ims_api
```

the output:

```bash
DETAIL:  Key (sku)=(test-sku) already exists.

[SQL: INSERT INTO products (name, sku) VALUES (%(name)s, %(sku)s) RETURNING products.id, products.created_at]
[parameters: {'name': 'test-product', 'sku': 'test-sku'}]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
```

- This shows that I already used the sku `test-sku` and this variable is unique.

- To prevent duplicates I added:

```bash
SKU="test-sku-$(date +%s)"
```

- This ensures that the test SKU will have a unique number following this pattern test-sku-XXXXX

[✓] Status: Solved. The test doesn't signal SKU errors now.

### BUG #2

- Inventory didn't update for test script `test_scripts/test_sc.sh`

- The error code:

```bash
Inventory response: {"product_id":9,"inventory":50}
FAIL: Expected inventory 50, got null
```
- ChatGPT said actual api response didn't match with the test script

- I replaced this

```bash
quantity=$(echo "$inventory" | jq -r '.quantity')
```

with this:

```bash
quantity=$(echo "$inventory" | jq -r '.inventory')
```

- Sent the code to chatgpt to have it fixed for the entire test

- The test passed.

[✓] Status: Solved. All the tests run successfully now.