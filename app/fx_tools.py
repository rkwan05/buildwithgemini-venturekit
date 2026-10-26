"""Public FX and currency conversion tool for VentureKit."""
import os
import urllib.request
import json
from typing import Any


def convert_currency_pricing(
    amount: float,
    base_currency: str = "USD",
    target_currencies: list[str] | None = None,
) -> dict[str, Any]:
    """Converts a price or revenue figure from a base currency to target international currencies using live exchange rates.

    Useful for small business owners pricing cross-border services, international client retainers, or foreign supplier COGS.

    Args:
        amount: The numerical amount to convert (e.g. 1500.0).
        base_currency: The standard 3-letter currency code of the input amount (default 'USD').
        target_currencies: Optional list of target 3-letter currency codes (e.g. ['EUR', 'GBP', 'CAD']).
                           Defaults to ['EUR', 'GBP', 'CAD', 'AUD'].

    Returns:
        A dictionary with original amount, converted amounts, and exchange rates.
    """
    base = base_currency.upper().strip()
    targets = [c.upper().strip() for c in (target_currencies or ["EUR", "GBP", "CAD", "AUD"])]

    # Uses the open ExchangeRate-API (free, reliable public API listed in public-apis)
    # Allows an optional custom API key via FX_API_KEY environment variable if needed.
    api_key = os.getenv("FX_API_KEY")
    if api_key:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
    else:
        url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VentureKit/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("result") != "success":
            return {"error": f"Failed to fetch exchange rates for {base}: {data.get('error-type', 'Unknown error')}"}

        all_rates = data.get("rates", {})
        converted = {}
        for target in targets:
            rate = all_rates.get(target)
            if rate is not None:
                converted[target] = {
                    "rate": round(rate, 4),
                    "converted_amount": round(amount * rate, 2),
                }

        return {
            "status": "success",
            "base_currency": base,
            "original_amount": amount,
            "conversions": converted,
            "last_updated": data.get("time_last_update_utc", "recent"),
        }
    except Exception as e:
        return {"status": "error", "message": f"Currency conversion error: {str(e)}"}
