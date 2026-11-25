"""Bes bekci: standart tablo saglam mi?"""

import re
from datetime import date

CURRENCIES = {"USD", "EUR", "CHF", "GBP", "JPY"}


def isin_is_valid(isin: str) -> bool:
    """Bicim + son hane (check digit) kontrolu."""
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin):
        return False
    digits = "".join(str(int(c, 36)) for c in isin[:-1])  # harfleri sayiya cevir: A=10 ...
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return (10 - total % 10) % 10 == int(isin[-1])


def check(rows, control_count, expected_accounts, business_date: date):
    """Sorun listesi dondurur. Bos liste = dosya saglam."""
    problems = []
    if not rows:                                                   # 1. HERE: bos mu?
        return ["Dosya bos"]
    if control_count is not None and control_count != len(rows):   # 3. WHOLE: sayi tutuyor mu?
        problems.append(f"Kontrol sayisi {control_count}, okunan satir {len(rows)}")
    missing = sorted(set(expected_accounts) - {r["account_id"] for r in rows})
    if missing:                                                    # 3. WHOLE: hesaplar tam mi?
        problems.append(f"Eksik hesaplar: {missing}")
    for r in rows:                                                 # 5. SANE: degerler mantikli mi?
        if not isin_is_valid(r["isin"]):
            problems.append(f"Gecersiz ISIN: {r['isin']}")
        if r["price"] <= 0:
            problems.append(f"Fiyat sifir/negatif: {r['isin']}")
        if r["currency"] not in CURRENCIES:
            problems.append(f"Bilinmeyen para birimi: {r['currency']}")
        if r["business_date"] != business_date:
            problems.append(f"Yanlis tarih: {r['business_date']}")
    return problems
