from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import httpx

from database import create_document, get_documents
from schemas import Game, Deal, Wishlist, Notification

app = FastAPI(title="Game Deals API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0"
EPIC_FREE_GAMES_API = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

class DealsResponse(BaseModel):
    items: List[Deal]
    total: int

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/games", response_model=List[Game])
async def list_games(q: Optional[str] = None, platform: Optional[str] = None, limit: int = 24):
    # Placeholder DB query. In a real implementation, aggregate from multiple sources and cache in DB.
    # Returning empty list for now to keep schema valid.
    docs = await get_documents("game", {}, limit)
    # Transform Mongo docs to Pydantic-compatible dicts
    items: List[Game] = []
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
        items.append(Game(**d))
    if q:
        items = [g for g in items if q.lower() in g.title.lower()]
    if platform:
        items = [g for g in items if platform in (g.platforms or [])]
    return items[:limit]

@app.get("/deals", response_model=DealsResponse)
async def deals(store: Optional[str] = None, page: int = 1, size: int = 24):
    # Integrate CheapShark as initial provider for PC deals
    params = {"pageNumber": page - 1, "pageSize": size}
    if store:
        params["storeID"] = store
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{CHEAPSHARK_API}/deals", params=params)
        r.raise_for_status()
        data = r.json()
    items: List[Deal] = []
    for d in data:
        items.append(
            Deal(
                id=d.get("dealID"),
                game_slug=d.get("title", "").lower().replace(" ", "-"),
                store=str(d.get("storeID")),
                price=float(d.get("salePrice", 0)),
                original_price=float(d.get("normalPrice", 0)),
                discount_pct=float(d.get("savings", 0)),
                currency="USD",
                url=f"https://www.cheapshark.com/redirect?dealID={d.get('dealID')}",
                ends_at=None,
            )
        )
    return DealsResponse(items=items, total=len(items))

@app.get("/epic/free")
async def epic_free_games():
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(EPIC_FREE_GAMES_API)
        r.raise_for_status()
        data = r.json()
    # Simplify Epic response
    items = []
    for elem in data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", []):
        promotions = elem.get("promotions") or {}
        offers = promotions.get("promotionalOffers") or promotions.get("upcomingPromotionalOffers") or []
        is_free = False
        if offers:
            for offer in offers[0].get("promotionalOffers", []):
                discount = offer.get("discountSetting", {}).get("discountPercentage", 0)
                if discount == 100:
                    is_free = True
        if is_free:
            items.append({
                "title": elem.get("title"),
                "productSlug": elem.get("productSlug"),
                "url": f"https://store.epicgames.com/p/{(elem.get('productSlug') or '').strip('/')}"
            })
    return {"items": items}

class WishlistIn(BaseModel):
    user_id: str
    game_slug: str

@app.post("/wishlist")
async def wishlist_add(body: WishlistIn):
    doc = await create_document("wishlist", body.model_dump())
    return {"ok": True, "item": {"id": doc.get("_id"), **body.model_dump()}}

@app.get("/wishlist/{user_id}")
async def wishlist_list(user_id: str):
    docs = await get_documents("wishlist", {"user_id": user_id}, 200)
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return {"items": docs}
