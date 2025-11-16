from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator


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
    ticker_symbol: str = ""
    company_name: str = ""
    added_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_company_fields(cls, data: Any) -> Any:
        """Populate ticker_symbol and company_name from company relationship"""
        if isinstance(data, dict):
            return data

        # data is a SQLAlchemy model instance with @property methods
        # Convert to dict and add computed fields
        if hasattr(data, 'company'):
            # Create a dict from the model's columns
            result = {
                'id': data.id,
                'watchlist_id': data.watchlist_id,
                'company_id': data.company_id,
                'display_order': data.display_order,
                'memo': data.memo,
                'tags': data.tags,
                'quantity': data.quantity,
                'purchase_price': data.purchase_price,
                'added_at': data.added_at,
                # Use the @property methods to get computed fields
                'ticker_symbol': data.ticker_symbol,
                'company_name': data.company_name,
            }
            return result

        return data


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
