from ingest.load import to_db_rows


def test_rows_are_in_insert_order_with_source_file():
    row = {"custodian": "UBS", "account_id": "A001", "isin": "US0378331005",
           "quantity": "81.0", "price": "189.5", "currency": "USD",
           "business_date": "2026-11-24"}
    assert to_db_rows([row], "x.csv") == [
        ("UBS", "A001", "US0378331005", "81.0", "189.5", "USD", "2026-11-24", "x.csv")
    ]
