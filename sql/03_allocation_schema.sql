/*
  Mirage allocation module: schema for the extra inputs.
  Target: SQL Server (T-SQL). Run after 00-02.
  Everything here is synthetic. See scripts/gen_allocation_data.py.
*/

IF OBJECT_ID('dbo.fact_dc_po', 'U') IS NOT NULL DROP TABLE dbo.fact_dc_po;
IF OBJECT_ID('dbo.fact_sales_daily', 'U') IS NOT NULL DROP TABLE dbo.fact_sales_daily;
IF OBJECT_ID('dbo.dim_sku_pack', 'U') IS NOT NULL DROP TABLE dbo.dim_sku_pack;
IF OBJECT_ID('dbo.dim_alloc_params', 'U') IS NOT NULL DROP TABLE dbo.dim_alloc_params;

-- Units sold per club, SKU and day. 28 days ending on the check day.
CREATE TABLE dbo.fact_sales_daily (
    sales_date  DATE NOT NULL,
    store_id    INT  NOT NULL,
    sku_id      INT  NOT NULL,
    units_sold  INT  NOT NULL,
    CONSTRAINT PK_fact_sales_daily PRIMARY KEY (sales_date, store_id, sku_id),
    CONSTRAINT FK_sales_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store (store_id),
    CONSTRAINT FK_sales_sku   FOREIGN KEY (sku_id)   REFERENCES dbo.dim_sku (sku_id)
);

-- Smallest quantity the DC can send a club. Allocation and transfers move whole cases.
CREATE TABLE dbo.dim_sku_pack (
    sku_id     INT NOT NULL PRIMARY KEY,
    case_pack  INT NOT NULL CHECK (case_pack > 0),
    CONSTRAINT FK_pack_sku FOREIGN KEY (sku_id) REFERENCES dbo.dim_sku (sku_id)
);

-- Inbound purchase order received at the DC (warehouse_4), in cases.
CREATE TABLE dbo.fact_dc_po (
    po_id           NVARCHAR(20) NOT NULL,
    dc_store_id     INT          NOT NULL,
    sku_id          INT          NOT NULL,
    receipt_date    DATE         NOT NULL,
    cases_received  INT          NOT NULL CHECK (cases_received >= 0),
    CONSTRAINT PK_fact_dc_po PRIMARY KEY (po_id, sku_id),
    CONSTRAINT FK_po_dc  FOREIGN KEY (dc_store_id) REFERENCES dbo.dim_store (store_id),
    CONSTRAINT FK_po_sku FOREIGN KEY (sku_id)      REFERENCES dbo.dim_sku (sku_id)
);

-- Planning rules, one row. Change a number here and every view follows.
CREATE TABLE dbo.dim_alloc_params (
    as_of_date          DATE         NOT NULL,
    sales_window_start  DATE         NOT NULL,
    sales_window_days   INT          NOT NULL,
    target_wos          DECIMAL(5,2) NOT NULL,  -- fill clubs up to this many weeks of supply
    donor_keep_wos      DECIMAL(5,2) NOT NULL,  -- a club giving stock away keeps at least this much
    overstock_wos       DECIMAL(5,2) NOT NULL,  -- above this, a club can give stock away
    receiver_wos        DECIMAL(5,2) NOT NULL   -- below this, a club gets stock from another club
);

/*
  Load the CSVs from data/ with BULK INSERT, the Import Flat File wizard, or Azure Data Studio:
    data/fact_sales_daily.csv -> dbo.fact_sales_daily
    data/dim_sku_pack.csv     -> dbo.dim_sku_pack
    data/fact_dc_po.csv       -> dbo.fact_dc_po
    data/dim_alloc_params.csv -> dbo.dim_alloc_params
*/
