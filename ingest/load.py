"""data/clean dosyalarini Postgres'teki bronze tablolarina yukler (idempotent)."""

import argparse
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()  # .env dosyasindaki sifreyi ortam degiskenine al

COLUMNS = ["custodian", "account_id", "isin", "quantity", "price", "currency", "business_date"]


def connect():
    return psycopg2.connect(host="127.0.0.1", port=5433, dbname="atlas", user="atlas",
                            password=os.environ["POSTGRES_PASSWORD"])


def to_db_rows(rows, source_file: str):
    """CSV satirlarini, INSERT'in bekledigi sirada tuple'lara cevir."""
    return [tuple(r[c] for c in COLUMNS) + (source_file,) for r in rows]


def load_positions(bank: str, business_date: str) -> int:
    path = Path("data/clean") / bank / business_date / "positions.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    conn = connect()
    try:
        with conn:                      # tek transaction: ya hepsi ya hicbiri
            with conn.cursor() as cur:
                cur.execute("DELETE FROM bronze.positions "
                            "WHERE custodian = %s AND business_date = %s",
                            (bank.upper(), business_date))           # once o gunu sil
                cur.executemany(
                    "INSERT INTO bronze.positions (custodian, account_id, isin, quantity, "
                    "price, currency, business_date, source_file) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    to_db_rows(rows, str(path)))                       # sonra yeniden ekle
                cur.execute("INSERT INTO ops.load_log (custodian, business_date, source_file, "
                            "row_count) VALUES (%s, %s, %s, %s)",
                            (bank.upper(), business_date, str(path), len(rows)))
    finally:
        conn.close()
    print(f"{bank.upper()} {business_date}: {len(rows)} satir bronze.positions'a yuklendi")
    return len(rows)


def load_reference() -> None:
    with Path("data/samples/ref/account_master.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            for r in rows:              # UPSERT: varsa guncelle, yoksa ekle
                cur.execute(
                    "INSERT INTO ref.accounts (account_id, custodian, client_key, is_active) "
                    "VALUES (%s, %s, %s, %s) ON CONFLICT (account_id) DO UPDATE SET "
                    "custodian = EXCLUDED.custodian, client_key = EXCLUDED.client_key, "
                    "is_active = EXCLUDED.is_active",
                    (r["account_id"], r["custodian"], r["client_key"], r["is_active"] == "true"))
    finally:
        conn.close()
    print(f"ref.accounts: {len(rows)} hesap")


def main():
    p = argparse.ArgumentParser(description="clean -> bronze yukleyici")
    p.add_argument("--bank", choices=["ubs", "jb", "pictet"])
    p.add_argument("--date", help="YYYY-MM-DD")
    p.add_argument("--ref", action="store_true", help="referans hesap listesini yukle")
    a = p.parse_args()
    if a.ref:
        load_reference()
    if a.bank:
        load_positions(a.bank, a.date)


if __name__ == "__main__":
    main()
