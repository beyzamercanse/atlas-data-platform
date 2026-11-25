"""Raw dosyayi oku, 5 bekciden gecir: gecerse clean'e, gecmezse karantinaya."""

import argparse
import csv
import shutil
from datetime import date
from pathlib import Path

from ingest.guards import check
from ingest.parse import STANDARD, SchemaError, parse

ACCOUNT_MASTER = Path("data/samples/ref/account_master.csv")


def expected_accounts(bank: str):
    with ACCOUNT_MASTER.open(encoding="utf-8", newline="") as f:
        return [r["account_id"] for r in csv.DictReader(f)
                if r["custodian"] == bank.upper() and r["is_active"] == "true"]


def run(bank: str, file: Path, business_date: str) -> bool:
    bdate = date.fromisoformat(business_date)
    try:
        rows, control = parse(file, bank)                          # 4. SAME SHAPE parser'da
        problems = check(rows, control, expected_accounts(bank), bdate)
    except (SchemaError, ValueError, KeyError) as e:
        rows, problems = [], [f"{type(e).__name__}: {e}"]

    if problems:                                                   # KARANTINA
        q = Path("data/quarantine") / bank / business_date
        q.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, q / file.name)
        (q / "problems.txt").write_text("\n".join(problems), encoding="utf-8")
        print(f"KARANTINA {file.name}:")
        for p in problems:
            print("  -", p)
        return False

    out = Path("data/clean") / bank / business_date / "positions.csv"  # GECTI
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=STANDARD)
        w.writeheader()
        w.writerows(rows)
    print(f"GECTI {file.name}: {len(rows)} satir -> {out}")
    return True


def main():
    p = argparse.ArgumentParser(description="Parse + 5 bekci")
    p.add_argument("--bank", required=True, choices=["ubs", "jb", "pictet"])
    p.add_argument("--file", required=True, type=Path)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    a = p.parse_args()
    raise SystemExit(0 if run(a.bank, a.file, a.date) else 1)


if __name__ == "__main__":
    main()
