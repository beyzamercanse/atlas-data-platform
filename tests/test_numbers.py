from ingest.numbers import parse_eu_number


def test_thousands_dot_and_decimal_comma():
    assert parse_eu_number("1.234,56") == 1234.56


def test_negative_in_parentheses():
    assert parse_eu_number("(150,00)") == -150.0


def test_simple_decimal():
    assert parse_eu_number("189,5") == 189.5
