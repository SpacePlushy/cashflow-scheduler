from cashflow.core.model import to_cents, cents_to_str


def test_money_roundtrip():
    assert to_cents(0) == 0
    assert to_cents(1.23) == 123
    assert to_cents("1.23") == 123
    assert cents_to_str(0) == "0.00"
    assert cents_to_str(123) == "1.23"
    assert cents_to_str(-123) == "-1.23"
