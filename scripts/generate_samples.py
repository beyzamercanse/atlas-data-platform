"""Atlas icin sahte ama gercekci banka dosyalari uretir.

Tum veriler uydurmadir, fiyatlar temsilidir. Gercek musteri verisi asla repoya girmez.
"""

import csv
import json
import random
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

BUSINESS_DATE = date(2026, 11, 24)
STAMP = BUSINESS_DATE.strftime("%Y%m%d")  # 20261124
OUT = Path("data/samples")

SECURITIES = [
    # (isin, ad, para birimi, fiyat, varlik sinifi)
    ("US0378331005", "Apple Inc", "USD", 189.50, "equity"),
    ("US5949181045", "Microsoft Corp", "USD", 415.20, "equity"),
    ("CH0038863350", "Nestle SA", "CHF", 98.50, "equity"),
    ("CH0012005267", "Novartis AG", "CHF", 87.30, "equity"),
    ("NL0010273215", "ASML Holding", "EUR", 642.10, "equity"),
    ("FR0000121014", "LVMH", "EUR", 701.40, "equity"),
    ("XS1234567896", "Example Corp 4% 2030", "EUR", 100.25, "bond"),
]

ACCOUNTS = {
    "ubs": ["A001", "A002", "A003", "A004"],
    "pictet": ["P001", "P002", "P003"],
    "jb": ["J001", "J002", "J003"],
}


def make_positions(accounts):
    """Her hesaba 3-5 rastgele menkul ver."""
    rows = []
    for acc in accounts:
        for isin, _name, ccy, price, asset in random.sample(SECURITIES, k=random.randint(3, 5)):
            if asset == "bond":
                qty = random.choice([10_000, 25_000, 50_000])  # tahvil: nominal tutar
            else:
                qty = random.randint(10, 500)  # hisse: adet
            rows.append(
                {"account_id": acc, "isin": isin, "quantity": float(qty),
                 "price": price, "currency": ccy}
            )
    return rows


def eu(number, decimals=2):
    """1234.56 -> '1.234,56' (Avrupa formati)."""
    s = f"{number:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fw_number(number, decimals, width=12):
    """Gizli ondalik: 189.5 (4 ondalik) -> '000001895000'."""
    return str(round(number * 10**decimals)).zfill(width)


def write_ubs(rows):
    folder = OUT / "ubs"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"UBS_POS_{STAMP}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["account_id", "isin", "quantity", "price", "currency", "business_date"])
        for r in rows:
            w.writerow([r["account_id"], r["isin"], eu(r["quantity"]), eu(r["price"], 4),
                        r["currency"], BUSINESS_DATE.strftime("%d.%m.%Y")])
    (folder / f"UBS_POS_{STAMP}.done").touch()  # "yazmayi bitirdim" isareti
    return path


def write_jb(rows):
    folder = OUT / "jb"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"JB_POS_{STAMP}.txt"
    lines = ["H" + "JB".ljust(10) + STAMP]  # header
    for r in rows:  # detail: tam 58 karakter
        lines.append("D" + r["account_id"].ljust(10) + r["isin"]
                     + fw_number(r["quantity"], 2) + fw_number(r["price"], 4)
                     + r["currency"] + STAMP)
    lines.append("T" + str(len(rows)).zfill(9))  # trailer: kac detay satiri var
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    (folder / f"JB_POS_{STAMP}.done").touch()
    return path


def write_pictet(rows):
    folder = OUT / "pictet"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"PICTET_POS_{STAMP}.xml"
    root = ET.Element("Statement", {"bank": "PICTET", "businessDate": BUSINESS_DATE.isoformat()})
    by_account = {}
    for r in rows:
        by_account.setdefault(r["account_id"], []).append(r)
    for acc, items in by_account.items():
        account = ET.SubElement(root, "Account", {"id": acc})
        for r in items:
            pos = ET.SubElement(account, "Position")
            ET.SubElement(pos, "ISIN").text = r["isin"]
            ET.SubElement(pos, "Quantity").text = f"{r['quantity']:.2f}"
            ET.SubElement(pos, "Price", {"currency": r["currency"]}).text = f"{r['price']:.4f}"
    ET.SubElement(root, "Summary", {"positionCount": str(len(rows))})
    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    (folder / f"PICTET_POS_{STAMP}.done").touch()
    return path


def write_prices():
    folder = OUT / "market"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"prices_{STAMP}.json"
    data = {
        "request_id": f"px-{STAMP}",
        "business_date": BUSINESS_DATE.isoformat(),
        "source": "SAMPLE_BLOOMBERG",
        "securities": [
            {"isin": i, "name": n, "currency": c, "px_last": p} for i, n, c, p, _ in SECURITIES
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def write_reference():
    folder = OUT / "ref"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "account_master.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["account_id", "custodian", "client_key", "is_active"])
        n = 1
        for bank, accounts in ACCOUNTS.items():
            for acc in accounts:
                w.writerow([acc, bank.upper(), f"C-{n:04d}", "true"])  # isim yok: GDPR
                n += 1
    with (folder / "security_master.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["isin", "name", "currency", "asset_class"])
        for isin, name, ccy, _price, asset in SECURITIES:
            w.writerow([isin, name, ccy, asset])


def main():
    random.seed(42)  # her calistirmada ayni dosyalar: testler tekrarlanabilir
    ubs = make_positions(ACCOUNTS["ubs"])
    jb = make_positions(ACCOUNTS["jb"])
    pictet = make_positions(ACCOUNTS["pictet"])
    print("UBS    :", write_ubs(ubs), f"({len(ubs)} satir)")
    print("JB     :", write_jb(jb), f"({len(jb)} satir)")
    print("Pictet :", write_pictet(pictet), f"({len(pictet)} pozisyon)")
    print("Fiyat  :", write_prices())
    write_reference()
    print("Ref    : data/samples/ref/account_master.csv, security_master.csv")


if __name__ == "__main__":
    main()
