"""Her bankanin formatini okuyup TEK bir standart tabloya cevirir."""

import csv
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml

from ingest.numbers import parse_eu_number

STANDARD = ["custodian", "account_id", "isin", "quantity", "price", "currency",
            "business_date"]


class SchemaError(Exception):
    """Dosyanin sekli tarif kartina uymuyor (bekci 4: ayni sekil mi?)."""


def load_config(bank: str) -> dict:
    return yaml.safe_load(Path(f"ingest/configs/{bank}.yaml").read_text(encoding="utf-8"))


def parse_csv(path: Path, cfg: dict):
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=cfg["delimiter"])
        header = next(reader)
        if header != cfg["columns"]:
            raise SchemaError(f"Kolonlar farkli. Beklenen {cfg['columns']}, gelen {header}")
        rows = [dict(zip(header, line)) for line in reader]
    for r in rows:
        r["quantity"] = parse_eu_number(r["quantity"])
        r["price"] = parse_eu_number(r["price"])
        r["business_date"] = datetime.strptime(r["business_date"], cfg["date_format"]).date()
    return rows, None


def parse_fixed_width(path: Path, cfg: dict):
    lines = path.read_text(encoding="ascii").splitlines()
    rows = []
    for line in [x for x in lines if x.startswith("D")]:
        if len(line) != cfg["record_length"]:
            raise SchemaError(f"Satir uzunlugu {len(line)}, beklenen {cfg['record_length']}")
        row = {}
        for name, spec in cfg["layout"].items():
            raw = line[spec[0]:spec[1]].strip()
            row[name] = int(raw) / 10 ** spec[2] if len(spec) == 3 else raw
        row["business_date"] = datetime.strptime(row["business_date"], cfg["date_format"]).date()
        rows.append(row)
    trailers = [x for x in lines if x.startswith("T")]
    control = int(trailers[-1][1:]) if trailers else None
    return rows, control


def parse_xml(path: Path, cfg: dict):
    root = ET.parse(path).getroot()
    bdate = datetime.strptime(root.get("businessDate"), "%Y-%m-%d").date()
    rows = []
    for account in root.findall("Account"):
        for p in account.findall("Position"):
            price = p.find("Price")
            rows.append({"account_id": account.get("id"), "isin": p.findtext("ISIN"),
                         "quantity": float(p.findtext("Quantity")), "price": float(price.text),
                         "currency": price.get("currency"), "business_date": bdate})
    summary = root.find("Summary")
    control = int(summary.get("positionCount")) if summary is not None else None
    return rows, control


PARSERS = {"csv": parse_csv, "fixed_width": parse_fixed_width, "xml": parse_xml}


def parse(path: Path, bank: str):
    """Dosyayi oku -> (standart satirlar, bankanin verdigi kontrol sayisi)."""
    cfg = load_config(bank)
    rows, control = PARSERS[cfg["format"]](path, cfg)
    for r in rows:
        r["custodian"] = bank.upper()
    return [{k: r[k] for k in STANDARD} for r in rows], control
