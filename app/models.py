from pydantic import BaseModel, Field


class LaptopOffer(BaseModel):
    title: str
    price: float
    currency: str = "EUR"
    item_url: str
    condition: str = "Unbekannt"
    location: str = "Unbekannt"


class EvaluatedOffer(LaptopOffer):
    verdict: str = Field(description="Geeignet, bedingt geeignet oder ungeeignet")
    confidence: int = Field(ge=0, le=100)
    reason: str
