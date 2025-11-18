from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

# Each model corresponds to a MongoDB collection (collection name = class name lowercased)

class Game(BaseModel):
    id: Optional[str] = Field(default=None)
    title: str
    slug: str
    platforms: List[str] = []
    genres: List[str] = []
    publishers: List[str] = []
    developers: List[str] = []
    release_date: Optional[datetime] = None
    cover_url: Optional[HttpUrl] = None
    screenshots: List[HttpUrl] = []
    trailers: List[HttpUrl] = []
    description: Optional[str] = None
    metacritic: Optional[int] = None
    opencritic: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Deal(BaseModel):
    id: Optional[str] = Field(default=None)
    game_slug: str
    store: str
    price: float
    original_price: Optional[float] = None
    discount_pct: Optional[float] = None
    currency: str = "USD"
    url: Optional[HttpUrl] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Wishlist(BaseModel):
    id: Optional[str] = Field(default=None)
    user_id: str
    game_slug: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Notification(BaseModel):
    id: Optional[str] = Field(default=None)
    user_id: str
    type: str  # "epic_free", "discount", etc.
    title: str
    message: str
    data: Optional[dict] = None
    delivered: bool = False
    created_at: Optional[datetime] = None

