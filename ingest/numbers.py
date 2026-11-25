def parse_eu_number(text: str) -> float:
    """Avrupa formatindaki sayiyi cevirir: '1.234,56' -> 1234.56, '(150,00)' -> -150.0"""
    s = text.strip()
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(".", "").replace(",", ".")
    value = float(s)
    return -value if negative else value
