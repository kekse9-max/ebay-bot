from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.ai_evaluator import AiEvaluator
from app.services.ebay_client import EbayClient

app = FastAPI(title="eBay Elden-Ring Checker (Kostenlos)")

base_dir = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=base_dir / "static"), name="static")
templates = Jinja2Templates(directory=str(base_dir / "templates"))


VERDICT_PRIORITY = {
    "geeignet": 0,
    "bedingt geeignet": 1,
    "ungeeignet": 2,
}


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    max_price: int = Query(default=200, ge=50, le=1000),
    item_type: Literal["laptop", "pc"] = Query(default="laptop"),
    evaluator: Literal["auto", "heuristic", "ollama"] = Query(default="auto"),
    sort_by: Literal["best", "price_asc", "price_desc"] = Query(default="best"),
    layout: Literal["grid", "compact"] = Query(default="grid"),
):
    ebay = EbayClient()
    ai = AiEvaluator(requested_mode=evaluator)

    offers = await ebay.search_items(item_type=item_type, max_price=max_price)
    evaluated = await ai.evaluate_for_elden_ring(offers)

    if sort_by == "best":
        evaluated = sorted(
            evaluated,
            key=lambda o: (VERDICT_PRIORITY.get(o.verdict, 99), -o.confidence, o.price),
        )
    elif sort_by == "price_asc":
        evaluated = sorted(evaluated, key=lambda o: (o.price, -o.confidence))
    else:
        evaluated = sorted(evaluated, key=lambda o: (-o.price, -o.confidence))

    counts = {
        "geeignet": sum(1 for o in evaluated if o.verdict == "geeignet"),
        "bedingt": sum(1 for o in evaluated if o.verdict == "bedingt geeignet"),
        "ungeeignet": sum(1 for o in evaluated if o.verdict == "ungeeignet"),
    }

    type_label = "Laptops" if item_type == "laptop" else "PCs"
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "offers": evaluated,
            "max_price": max_price,
            "counts": counts,
            "item_type": item_type,
            "type_label": type_label,
            "using_mock": not bool(ebay.token),
            "evaluator_mode": ai.mode,
            "requested_evaluator": evaluator,
            "sort_by": sort_by,
            "layout": layout,
        },
    )
