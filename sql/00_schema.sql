/*
  Mirage — pass 1 schema
  Target: SQL Server (T-SQL). Portable types. Synthetic club retail.
  Map pins use real city lat/long so the glance map is honest.
*/

IF OBJECT_ID('dbo.fact_inventory_daily', 'U') IS NOT NULL DROP TABLE dbo.fact_inventory_daily;
IF OBJECT_ID('dbo.dim_sku', 'U') IS NOT NULL DROP TABLE dbo.dim_sku;
IF OBJECT_ID('dbo.dim_store', 'U') IS NOT NULL DROP TABLE dbo.dim_store;

CREATE TABLE dbo.dim_store (
    store_id        INT            NOT NULL PRIMARY KEY,
    store_name      NVARCHAR(80)   NOT NULL,
    region          NVARCHAR(40)   NOT NULL,
    format_type     NVARCHAR(40)   NOT NULL,  -- club / crossdock
    city            NVARCHAR(80)   NOT NULL,
    lat             DECIMAL(9, 6)  NOT NULL,
    lon             DECIMAL(9, 6)  NOT NULL,
    map_label       NVARCHAR(120)  NOT NULL,
    chip_label      NVARCHAR(40)   NOT NULL
);

CREATE TABLE dbo.dim_sku (
    sku_id          INT           NOT NULL PRIMARY KEY,
    sku_name        NVARCHAR(120) NOT NULL,
    category        NVARCHAR(60)  NOT NULL,
    subcategory     NVARCHAR(60)  NOT NULL,
    is_in_assortment BIT          NOT NULL DEFAULT 1
);

CREATE TABLE dbo.fact_inventory_daily (
    snapshot_date       DATE            NOT NULL,
    store_id            INT             NOT NULL,
    sku_id              INT             NOT NULL,
    floor_qty           DECIMAL(12, 2)  NOT NULL,
    backroom_qty        DECIMAL(12, 2)  NOT NULL,
    system_on_hand_qty  DECIMAL(12, 2)  NOT NULL,
    CONSTRAINT PK_fact_inventory_daily PRIMARY KEY (snapshot_date, store_id, sku_id),
    CONSTRAINT FK_inv_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store (store_id),
    CONSTRAINT FK_inv_sku   FOREIGN KEY (sku_id)   REFERENCES dbo.dim_sku (sku_id)
);

CREATE INDEX IX_fact_inventory_daily_store_date
    ON dbo.fact_inventory_daily (store_id, snapshot_date);
