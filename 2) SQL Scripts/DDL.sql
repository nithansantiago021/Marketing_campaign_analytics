-- =============================================================================
-- PART 1: DDL — Table Creation
--  This block lets you recreate it manually if needed.
-- =============================================================================

DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    -- Identity
    ID                      BIGINT       NOT NULL,
    Year_Birth              INT          NOT NULL,
    Education               VARCHAR(50)  NOT NULL,
    Marital_Status          VARCHAR(30)  NOT NULL,
    Income                  DOUBLE       NOT NULL,
    Kidhome                 TINYINT      NOT NULL DEFAULT 0,
    Teenhome                TINYINT      NOT NULL DEFAULT 0,
    Dt_Customer             VARCHAR(10)  NOT NULL,   -- 'YYYY-MM-DD' string
    Recency                 INT          NOT NULL,
    Country                 VARCHAR(50)  NOT NULL,
    Complain                TINYINT      NOT NULL DEFAULT 0,

    -- Spending columns
    MntWines                INT          NOT NULL DEFAULT 0,
    MntFruits               INT          NOT NULL DEFAULT 0,
    MntMeatProducts         INT          NOT NULL DEFAULT 0,
    MntFishProducts         INT          NOT NULL DEFAULT 0,
    MntSweetProducts        INT          NOT NULL DEFAULT 0,
    MntGoldProds            INT          NOT NULL DEFAULT 0,

    -- Channel purchases
    NumDealsPurchases       INT          NOT NULL DEFAULT 0,
    NumWebPurchases         INT          NOT NULL DEFAULT 0,
    NumCatalogPurchases     INT          NOT NULL DEFAULT 0,
    NumStorePurchases       INT          NOT NULL DEFAULT 0,
    NumWebVisitsMonth       INT          NOT NULL DEFAULT 0,

    -- Campaign acceptance flags (0/1)
    AcceptedCmp1            TINYINT      NOT NULL DEFAULT 0,
    AcceptedCmp2            TINYINT      NOT NULL DEFAULT 0,
    AcceptedCmp3            TINYINT      NOT NULL DEFAULT 0,
    AcceptedCmp4            TINYINT      NOT NULL DEFAULT 0,
    AcceptedCmp5            TINYINT      NOT NULL DEFAULT 0,
    Response                TINYINT      NOT NULL DEFAULT 0,

    -- Derived / engineered features (populated by Python pipeline)
    Age                     INT,
    Customer_Tenure_Days    INT,
    Customer_Tenure_Months  INT,
    Total_Spend             DOUBLE,
    Total_Purchases         INT,
    Children                TINYINT,
    Total_Campaign_Accepted TINYINT,
    Any_Campaign_Accepted   TINYINT,
    Age_Band                VARCHAR(10),
    Income_Band             VARCHAR(15),
    Primary_Segment         VARCHAR(30),

    -- Segment flag columns
    Seg_High_Income         TINYINT      DEFAULT 0,
    Seg_Young_Customer      TINYINT      DEFAULT 0,
    Seg_Campaign_Responder  TINYINT      DEFAULT 0,
    Seg_High_Web_Engagement TINYINT      DEFAULT 0,
    Seg_Family_Customer     TINYINT      DEFAULT 0,
    Seg_High_Spender        TINYINT      DEFAULT 0,

    PRIMARY KEY (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE INDEX idx_country      ON customers (Country);
CREATE INDEX idx_education    ON customers (Education);
CREATE INDEX idx_marital      ON customers (Marital_Status);
CREATE INDEX idx_segment      ON customers (Primary_Segment);
CREATE INDEX idx_age_band     ON customers (Age_Band);
CREATE INDEX idx_income_band  ON customers (Income_Band);
CREATE INDEX idx_response     ON customers (Response);