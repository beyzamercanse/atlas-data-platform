from datetime import date

import pytest

from ingest.guards import check, isin_is_valid
from ingest.parse import SchemaError, parse


def test_real_isins_are_valid():
    assert isin_is_valid("US0378331005")
    assert isin_is_valid("CH0038863350")


def test_one_wrong_digit_makes_isin_invalid():
    assert not isin_is_valid("US0378331006")


def test_fixed_width_implied_decimals(tmp_path):
    line = "DJ001      US0378331005000000015000000001895000USD20261124"
    f = tmp_path / "jb.txt"
    f.write_text("HJB        20261124\n" + line + "\nT000000001\n", encoding="ascii")
    rows, control = parse(f, "jb")
    assert rows[0]["quantity"] == 150.0
    assert rows[0]["price"] == 189.5
    assert control == 1


def test_new_csv_column_raises_schema_error(tmp_path):
    f = tmp_path / "ubs.csv"
    f.write_text("account_id;isin;quantity;price;currency;settle_ccy;business_date\n",
                 encoding="utf-8")
    with pytest.raises(SchemaError):
        parse(f, "ubs")


def test_missing_account_and_wrong_count_are_caught():
    rows = [{"account_id": "A001", "isin": "US0378331005", "quantity": 1.0, "price": 189.5,
             "currency": "USD", "business_date": date(2026, 11, 24)}]
    problems = check(rows, control_count=2, expected_accounts=["A001", "A002"],
                     business_date=date(2026, 11, 24))
    assert any("Kontrol sayisi" in p for p in problems)
    assert any("A002" in p for p in problems)
