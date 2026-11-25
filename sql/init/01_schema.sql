CREATE SCHEMA IF NOT EXISTS bronze;   -- bankadan gelen, kontrol edilmis veri
CREATE SCHEMA IF NOT EXISTS ref;      -- referans veri (hesap listesi)
CREATE SCHEMA IF NOT EXISTS ops;      -- operasyon kayitlari

CREATE TABLE IF NOT EXISTS bronze.positions (
    custodian      TEXT           NOT NULL,
    account_id     TEXT           NOT NULL,
    isin           TEXT           NOT NULL,
    quantity       NUMERIC(20,4)  NOT NULL,
    price          NUMERIC(20,6)  NOT NULL,
    currency       CHAR(3)        NOT NULL,
    business_date  DATE           NOT NULL,
    source_file    TEXT           NOT NULL,
    loaded_at      TIMESTAMPTZ    NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ref.accounts (
    account_id  TEXT PRIMARY KEY,
    custodian   TEXT,
    client_key  TEXT,
    is_active   BOOLEAN
);

CREATE TABLE IF NOT EXISTS ops.load_log (
    custodian      TEXT,
    business_date  DATE,
    source_file    TEXT,
    row_count      INT,
    loaded_at      TIMESTAMPTZ DEFAULT now()
);
