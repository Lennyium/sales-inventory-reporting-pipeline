
DROP VIEW IF EXISTS vw_monthly_sales;
DROP VIEW IF EXISTS vw_product_performance;
DROP VIEW IF EXISTS vw_country_performance;
DROP VIEW IF EXISTS vw_product_descriptions;

-- Monthly reporting: separate sales, non-cancellation negatives,
-- and cancellation invoice amounts.

DROP VIEW IF EXISTS vw_monthly_sales;

CREATE VIEW vw_monthly_sales AS
SELECT
    strftime('%Y-%m', InvoiceDate) AS sales_month,

    COUNT(DISTINCT CASE
        WHEN is_cancellation_invoice = 0 THEN InvoiceNo
    END) AS non_cancellation_invoice_count,

    ROUND(SUM(CASE
        WHEN is_cancellation_invoice = 0
         AND Quantity > 0
         AND UnitPrice > 0
        THEN LineAmount ELSE 0
    END), 2) AS positive_sales_line_amount,

    ROUND(SUM(CASE
        WHEN is_cancellation_invoice = 1
        THEN LineAmount ELSE 0
    END), 2) AS cancellation_line_amount,

    SUM(CASE
        WHEN is_cancellation_invoice = 0
         AND Quantity < 0
         AND UnitPrice = 0
        THEN 1 ELSE 0
    END) AS zero_price_negative_adjustment_lines,

    SUM(CASE
        WHEN is_cancellation_invoice = 0
         AND Quantity < 0
         AND UnitPrice = 0
        THEN ABS(Quantity) ELSE 0
    END) AS units_in_zero_price_negative_adjustments

FROM transactions
GROUP BY strftime('%Y-%m', InvoiceDate);



-- Choose the most common nonblank description for each stock code.
CREATE VIEW vw_product_descriptions AS
WITH description_counts AS (
    SELECT
        StockCode,
        Description,
        COUNT(*) AS description_count
    FROM transactions
    WHERE Description IS NOT NULL
      AND TRIM(Description) <> ''
    GROUP BY StockCode, Description
),
ranked_descriptions AS (
    SELECT
        StockCode,
        Description,
        ROW_NUMBER() OVER (
            PARTITION BY StockCode
            ORDER BY description_count DESC, Description ASC
        ) AS description_rank
    FROM description_counts
)
SELECT StockCode, Description AS product_description
FROM ranked_descriptions
WHERE description_rank = 1;


CREATE VIEW vw_product_performance AS
SELECT
    t.StockCode,
    d.product_description,
    SUM(t.Quantity) AS net_quantity,
    ROUND(SUM(t.LineAmount), 2) AS net_line_amount,
    COUNT(DISTINCT t.InvoiceNo) AS invoice_count
FROM transactions t
LEFT JOIN vw_product_descriptions d
    ON t.StockCode = d.StockCode
WHERE t.is_cancellation_invoice = 0
GROUP BY t.StockCode, d.product_description;


CREATE VIEW vw_country_performance AS
SELECT
    Country,
    COUNT(DISTINCT InvoiceNo) AS invoice_count,
    COUNT(DISTINCT CustomerID) AS customer_count,
    ROUND(SUM(LineAmount), 2) AS net_line_amount
FROM transactions
WHERE is_cancellation_invoice = 0
GROUP BY Country;
