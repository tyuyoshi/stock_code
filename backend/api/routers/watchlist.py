from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.auth import get_current_user
from core.rate_limiter import limiter, RateLimits
from models.user import User
from models.watchlist import Watchlist, WatchlistItem
from models.company import Company
from schemas.watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistDetailResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
)

router = APIRouter(
    prefix="/api/v1/watchlists",
    tags=["watchlists"],
    responses={404: {"description": "Not found"}},
)

PLAN_LIMITS = {
    "free": {"max_watchlists": 1, "max_items_per_watchlist": 20},
    "premium": {"max_watchlists": 10, "max_items_per_watchlist": 100},
    "enterprise": {"max_watchlists": None, "max_items_per_watchlist": None},
}


def check_watchlist_limit(user: User, db: Session):
    limits = PLAN_LIMITS.get(user.role, PLAN_LIMITS["free"])
    if limits["max_watchlists"] is None:
        return

    watchlist_count = db.query(Watchlist).filter(Watchlist.user_id == user.id).count()
    if watchlist_count >= limits["max_watchlists"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Plan limit reached: {user.role} plan allows maximum {limits['max_watchlists']} watchlists",
        )


def check_item_limit(watchlist: Watchlist, user: User, db: Session):
    limits = PLAN_LIMITS.get(user.role, PLAN_LIMITS["free"])
    if limits["max_items_per_watchlist"] is None:
        return

    item_count = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist.id)
        .count()
    )
    if item_count >= limits["max_items_per_watchlist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Plan limit reached: {user.role} plan allows maximum {limits['max_items_per_watchlist']} items per watchlist",
        )


def get_watchlist_by_id(watchlist_id: int, user: User, db: Session) -> Watchlist:
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found"
        )
    if watchlist.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this watchlist",
        )
    return watchlist


@router.get("/", response_model=List[WatchlistResponse])
@limiter.limit(RateLimits.STANDARD)
async def get_watchlists(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlists = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.display_order, Watchlist.created_at)
        .all()
    )
    return watchlists


@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.STANDARD)
async def create_watchlist(
    request: Request,
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_watchlist_limit(current_user, db)

    watchlist = Watchlist(
        user_id=current_user.id,
        name=watchlist_data.name,
        description=watchlist_data.description,
        is_public=watchlist_data.is_public,
        display_order=watchlist_data.display_order,
    )
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    return watchlist


@router.get("/{watchlist_id}", response_model=WatchlistDetailResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_watchlist(
    request: Request,
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id)
        .options(joinedload(Watchlist.items))
        .first()
    )
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found"
        )
    if watchlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this watchlist",
        )
    return watchlist


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
@limiter.limit(RateLimits.STANDARD)
async def update_watchlist(
    request: Request,
    watchlist_id: int,
    watchlist_data: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = get_watchlist_by_id(watchlist_id, current_user, db)

    update_data = watchlist_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(watchlist, field, value)

    db.commit()
    db.refresh(watchlist)
    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RateLimits.STANDARD)
async def delete_watchlist(
    request: Request,
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = get_watchlist_by_id(watchlist_id, current_user, db)
    db.delete(watchlist)
    db.commit()


@router.post(
    "/{watchlist_id}/stocks",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(RateLimits.STANDARD)
async def add_stock_to_watchlist(
    request: Request,
    watchlist_id: int,
    item_data: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = get_watchlist_by_id(watchlist_id, current_user, db)
    check_item_limit(watchlist, current_user, db)

    company = db.query(Company).filter(Company.id == item_data.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    existing_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.company_id == item_data.company_id,
        )
        .first()
    )
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company already exists in this watchlist",
        )

    watchlist_item = WatchlistItem(
        watchlist_id=watchlist_id,
        company_id=item_data.company_id,
        display_order=item_data.display_order,
        memo=item_data.memo,
        tags=item_data.tags,
        quantity=item_data.quantity,
        purchase_price=item_data.purchase_price,
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item


@router.delete(
    "/{watchlist_id}/stocks/{company_id}", status_code=status.HTTP_204_NO_CONTENT
)
@limiter.limit(RateLimits.STANDARD)
async def remove_stock_from_watchlist(
    request: Request,
    watchlist_id: int,
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlist = get_watchlist_by_id(watchlist_id, current_user, db)

    watchlist_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.company_id == company_id,
        )
        .first()
    )
    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in this watchlist",
        )

    db.delete(watchlist_item)
    db.commit()
