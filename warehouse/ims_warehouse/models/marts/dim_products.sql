-- Dimension table: one row per product
-- Source: dim_products.parquet built from PostgreSQL via make warehouse

SELECT
    product_id,
    name,
    sku,
    created_at
FROM read_parquet('{{ env_var("WAREHOUSE_ROOT", "/home/sinan/Desktop/projects/ims-manual/warehouse") }}/dim_products.parquet')
