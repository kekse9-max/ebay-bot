import json
import os
import re
from typing import Iterable, List, Tuple

import httpx

from app.models import EvaluatedOffer, LaptopOffer


class AiEvaluator:
    """Lokale Bewertung: Heuristik + optionales Ollama-LokallLM (beides kostenlos)."""

    def __init__(self, requested_mode: str = "auto") -> None:
        self.requested_mode = requested_mode
        self.ollama_url = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.mode = "heuristic"

    async def evaluate_for_elden_ring(self, offers: Iterable[LaptopOffer]) -> List[EvaluatedOffer]:
        offer_list = list(offers)
        if not offer_list:
            self.mode = "heuristic"
            return []

        if self.requested_mode in {"auto", "ollama"}:
            ollama_result = await self._evaluate_with_ollama(offer_list)
            if ollama_result is not None:
                self.mode = "ollama-local"
                return ollama_result

        self.mode = "heuristic"
        return [self._rule_based_evaluation(offer) for offer in offer_list]

    async def _evaluate_with_ollama(self, offers: List[LaptopOffer]) -> List[EvaluatedOffer] | None:
        prompt = self._build_ollama_prompt(offers)
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1},
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                response.raise_for_status()
            raw = response.json().get("response", "")
            parsed = json.loads(raw)
            if not isinstance(parsed, list) or len(parsed) != len(offers):
                return None

            evaluated: List[EvaluatedOffer] = []
            for offer, item in zip(offers, parsed):
                confidence = int(item.get("confidence", 50))
                confidence = max(0, min(100, confidence))
                verdict = str(item.get("verdict", "ungeeignet")).strip().lower()
                if verdict not in {"geeignet", "bedingt geeignet", "ungeeignet"}:
                    verdict = "ungeeignet"

                evaluated.append(
                    EvaluatedOffer(
                        **offer.model_dump(),
                        verdict=verdict,
                        confidence=confidence,
                        reason=str(item.get("reason", "Keine Begründung vorhanden.")),
                    )
                )
            return evaluated
        except Exception:
            return None

    def _build_ollama_prompt(self, offers: List[LaptopOffer]) -> str:
        serialized = [offer.model_dump() for offer in offers]
        min_requirements = {
            "cpu": "Intel Core i5-8400 oder AMD Ryzen 3 3300X",
            "ram": "12 GB",
            "gpu": "NVIDIA GTX 1060 3GB / AMD RX 580 4GB oder besser",
        }
        return (
            "Du bist Hardware-Experte. Prüfe jedes Angebot auf Elden-Ring-Tauglichkeit. "
            "Berücksichtige die Mindestanforderungen und gib eine konservative, realistische Einschätzung. "
            "Wenn wichtige Daten fehlen, bewerte eher vorsichtig. "
            "Antworte nur als JSON-Array gleicher Länge mit Objekten: "
            "{verdict: geeignet|bedingt geeignet|ungeeignet, confidence: 0-100, reason: string}.\n"
            f"Mindestanforderungen: {json.dumps(min_requirements, ensure_ascii=False)}\n"
            f"Angebote: {json.dumps(serialized, ensure_ascii=False)}"
        )

    def _rule_based_evaluation(self, offer: LaptopOffer) -> EvaluatedOffer:
        title = offer.title.lower()
        score = 15
        reasons: List[str] = []

        ram_score, ram_reason = self._score_ram(title)
        score += ram_score
        reasons.append(ram_reason)

        cpu_score, cpu_reason = self._score_cpu(title)
        score += cpu_score
        reasons.append(cpu_reason)

        gpu_score, gpu_reason = self._score_gpu(title)
        score += gpu_score
        reasons.append(gpu_reason)

        if any(token in title for token in ("defekt", "ohne funktion", "für bastler")):
            score -= 45
            reasons.append("Warnsignal: möglicher Defekt")

        if "ssd" in title:
            score += 3
            reasons.append("SSD erwähnt")

        score = max(0, min(100, score))

        if score >= 75:
            verdict = "geeignet"
        elif score >= 50:
            verdict = "bedingt geeignet"
        else:
            verdict = "ungeeignet"

        reason = ", ".join(reasons)
        return EvaluatedOffer(**offer.model_dump(), verdict=verdict, confidence=score, reason=reason)

    def _score_ram(self, title: str) -> Tuple[int, str]:
        match = re.search(r"(\d{1,2})\s?gb", title)
        if not match:
            return (-10, "RAM unbekannt")

        ram = int(match.group(1))
        if ram >= 16:
            return (26, f"{ram}GB RAM (über Mindestanforderung)")
        if ram >= 12:
            return (18, f"{ram}GB RAM (Mindestanforderung erfüllt)")
        if ram >= 8:
            return (3, f"{ram}GB RAM (unter Empfehlung)")
        return (-24, f"{ram}GB RAM (zu wenig)")

    def _score_cpu(self, title: str) -> Tuple[int, str]:
        cpu_map = {
            "i9": 34,
            "i7-12": 32,
            "i7-11": 30,
            "i7-10": 28,
            "i7-9": 25,
            "i7-8": 22,
            "i5-12": 30,
            "i5-11": 28,
            "i5-10": 25,
            "i5-9": 22,
            "i5-8": 20,
            "ryzen 9": 34,
            "ryzen 7": 28,
            "ryzen 5 5": 24,
            "ryzen 5 4": 22,
            "ryzen 5 3": 20,
            "ryzen 3 3": 16,
            "i3": -14,
            "celeron": -26,
            "pentium": -22,
            "atom": -30,
        }
        for token, points in cpu_map.items():
            if token in title:
                return (points, f"CPU-Hinweis '{token}'")
        return (0, "CPU unklar")

    def _score_gpu(self, title: str) -> Tuple[int, str]:
        gpu_map = {
            "rtx 40": 40,
            "rtx 30": 36,
            "rtx 20": 32,
            "gtx 1080": 32,
            "gtx 1070": 30,
            "gtx 1660": 28,
            "gtx 1060": 24,
            "gtx 1650": 18,
            "gtx 1050 ti": 12,
            "gtx 1050": 8,
            "rx 6600": 32,
            "rx 580": 24,
            "rx 570": 20,
            "mx550": 10,
            "mx450": 8,
            "mx350": 4,
            "mx250": 1,
            "mx150": -2,
            "intel arc": 18,
            "intel iris xe": 0,
            "intel uhd": -14,
            "vega 8": -8,
        }
        for token, points in gpu_map.items():
            if token in title:
                return (points, f"GPU-Hinweis '{token}'")

        if "gaming" in title:
            return (5, "'gaming' im Titel")
        return (-10, "dedizierte GPU nicht erkennbar")
