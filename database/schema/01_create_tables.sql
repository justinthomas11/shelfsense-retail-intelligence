CREATE TABLE IF NOT EXISTS dim_retailer (
    retailer_id   SERIAL PRIMARY KEY,
    retailer_name VARCHAR(50) NOT NULL UNIQUE,
    retailer_type VARCHAR(30),
    website_url   VARCHAR(200),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    parent_category VARCHAR(100),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id    SERIAL PRIMARY KEY,
    product_name  VARCHAR(300) NOT NULL,
    brand         VARCHAR(100),
    unit_size     VARCHAR(50),
    category_id   INTEGER REFERENCES dim_category(category_id),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_price_history (
    price_id      SERIAL PRIMARY KEY,
    product_id    INTEGER NOT NULL REFERENCES dim_product(product_id),
    retailer_id   INTEGER NOT NULL REFERENCES dim_retailer(retailer_id),
    price_date    DATE NOT NULL,
    mrp           NUMERIC(10,2),
    selling_price NUMERIC(10,2) NOT NULL,
    discount_pct  NUMERIC(5,2),
    is_available  BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, retailer_id, price_date)
);

CREATE TABLE IF NOT EXISTS fact_macro_cpi (
    cpi_id        SERIAL PRIMARY KEY,
    report_month  DATE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    cpi_index     NUMERIC(8,2),
    yoy_inflation NUMERIC(5,2),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_month, category_name)
);

CREATE INDEX idx_price_date ON fact_price_history(price_date);
CREATE INDEX idx_price_product ON fact_price_history(product_id);
CREATE INDEX idx_price_retailer ON fact_price_history(retailer_id);
CREATE INDEX idx_price_product_retailer_date 
    ON fact_price_history(product_id, retailer_id, price_date);
CREATE INDEX idx_cpi_month ON fact_macro_cpi(report_month);
