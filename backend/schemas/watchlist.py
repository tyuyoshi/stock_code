from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class WatchlistItemBase(BaseModel):
    company_id: int
    display_order: int = 0
    memo: Optional[str] = None
    tags: Optional[List[str]] = None
    quantity: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None


class WatchlistItemCreate(WatchlistItemBase):
    pass


class WatchlistItemUpdate(BaseModel):
    display_order: Optional[int] = None
    memo: Optional[str] = None
    tags: Optional[List[str]] = None
    quantity: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None


class WatchlistItemResponse(WatchlistItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_id: int
    added_at: datetime


class WatchlistBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_public: bool = False
    display_order: int = 0


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    display_order: Optional[int] = None


class WatchlistResponse(WatchlistBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class WatchlistDetailResponse(WatchlistResponse):
    model_config = ConfigDict(from_attributes=True)

    items: List[WatchlistItemResponse] = []
