-- warehouse/queries.sql

-- Query 1: Daily inventory delta
-- "How much did stock change per product per day?"
SELECT product_id, date_id, SUM(quantity) AS daily_delta
FROM fact_inventory_events
GROUP BY product_id, date_id
ORDER BY date_id, product_id

-- Query 2: Event type breakdown  
-- "Which event types are happening most and what is their total impact?"
SELECT 
    event_type,
    COUNT(*) AS event_count,
    SUM(quantity) AS total_quantity
FROM fact_inventory_events
GROUP BY event_type
ORDER BY COUNT(*) DESC

-- Query 3: Running inventory balance
-- "What was the stock level of each product at any point in time?"
SELECT
    product_id,
    date_id,
    quantity,
    SUM(quantity) OVER (
        PARTITION BY product_id
        ORDER BY date_id ASC
    ) AS running_balance
FROM fact_inventory_events
ORDER BY product_id, date_id