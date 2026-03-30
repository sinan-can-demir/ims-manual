SELECT
    e.event_id,
    e.product_id,
    e.date_id,
    e.event_type,
    e.quantity,
    e.created_at
FROM {{ ref('stg_inventory_events') }} e
JOIN {{ ref('dim_products') }} p
    ON e.product_id = p.product_id
