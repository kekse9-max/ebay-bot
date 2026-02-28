import os
from typing import List, Literal

import httpx

from app.models import LaptopOffer

EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SearchType = Literal["laptop", "pc"]


class EbayClient:
    def __init__(self) -> None:
        self.token = os.getenv("EBAY_BEARER_TOKEN")

    async def search_items(self, item_type: SearchType = "laptop", max_price: int = 200, limit: int = 12) -> List[LaptopOffer]:
        """Sucht Angebote (Laptop/PC) bis max_price in EUR."""
        if not self.token:
            return self._mock_results(item_type=item_type, max_price=max_price)

        search_term = "laptop" if item_type == "laptop" else "gaming pc"
        params = {
            "q": search_term,
            "limit": min(limit, 50),
            "filter": f"price:[..{max_price}],priceCurrency:EUR",
            "sort": "price",
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(EBAY_SEARCH_URL, params=params, headers=headers)
            response.raise_for_status()

        data = response.json()
        offers: List[LaptopOffer] = []
        for item in data.get("itemSummaries", []):
            price = item.get("price", {})
            offers.append(
                LaptopOffer(
                    title=item.get("title", "Ohne Titel"),
                    price=float(price.get("value", 0)),
                    currency=price.get("currency", "EUR"),
                    item_url=item.get("itemWebUrl", "#"),
                    condition=item.get("condition", "Unbekannt"),
                    location=item.get("itemLocation", {}).get("country", "Unbekannt"),
                )
            )
        return offers

    def _mock_results(self, item_type: SearchType, max_price: int) -> List[LaptopOffer]:
        """Fallback, falls kein eBay-Token gesetzt ist."""
        if item_type == "pc":
            return [
                LaptopOffer(
                    title="Gaming PC Ryzen 5 3600 16GB RAM GTX 1660",
                    price=min(max_price, 200),
                    currency="EUR",
                    item_url="https://www.ebay.de/",
                    condition="Gebraucht",
                    location="DE",
                ),
                LaptopOffer(
                    title="Office PC Intel i5-8500 8GB RAM Intel UHD",
                    price=129,
                    currency="EUR",
                    item_url="https://www.ebay.de/",
                    condition="Gebraucht",
                    location="DE",
                ),
                LaptopOffer(
                    title="Gaming Rechner i7-8700 16GB RAM GTX 1070",
                    price=199,
                    currency="EUR",
                    item_url="https://www.ebay.de/",
                    condition="Refurbished",
                    location="DE",
                ),
            ]

        return [
            LaptopOffer(
                title="Lenovo ThinkPad T480 i5-8250U 16GB RAM",
                price=199,
                currency="EUR",
                item_url="https://www.ebay.de/",
                condition="Gebraucht",
                location="DE",
            ),
            LaptopOffer(
                title="HP 250 G7 Intel i3-7020U 8GB RAM",
                price=179,
                currency="EUR",
                item_url="https://www.ebay.de/",
                condition="Gebraucht",
                location="DE",
            ),
            LaptopOffer(
                title="Dell Latitude 5590 i5-8350U 16GB RAM",
                price=min(max_price, 200),
                currency="EUR",
                item_url="https://www.ebay.de/",
                condition="Refurbished",
                location="DE",
            ),
        ]
