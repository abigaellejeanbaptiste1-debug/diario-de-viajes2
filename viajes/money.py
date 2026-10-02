from decimal import Decimal


def format_clp(amount: Decimal | int | str) -> str:
    """Format an amount as Chilean pesos, with dots as thousands separators."""
    return f"${Decimal(amount):,.0f}".replace(",", ".")
