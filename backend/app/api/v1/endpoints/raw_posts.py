from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from app.db.session import get_database
from app.db.repositories.raw_post import RawPostRepository
from app.schemas.raw_post import RawPostListResponse, RawPostResponse

router = APIRouter()


@router.get("", response_model=RawPostListResponse, summary="List & Filter Raw Posts")
async def list_raw_posts(
    limit: int = Query(default=50, ge=1, le=200, description="Page limit (1-200)"),
    skip: int = Query(default=0, ge=0, description="Page skip offset"),
    source: Optional[str] = Query(default=None, description="Filter by source name (e.g. bbc, telegram)"),
    processing_status: Optional[str] = Query(default=None, description="Filter by status: pending, processed, failed, duplicate"),
):
    """Retrieve raw posts with source filtering, status filtering, and pagination."""
    if processing_status and processing_status not in {"pending", "processed", "failed", "duplicate"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid processing_status value. Allowed values: pending, processed, failed, duplicate.",
        )

    db = get_database()
    raw_post_repo = RawPostRepository(db)

    posts = await raw_post_repo.list_posts(
        limit=limit,
        skip=skip,
        source=source,
        processing_status=processing_status,
    )
    total = await raw_post_repo.count_posts(
        source=source,
        processing_status=processing_status,
    )

    return RawPostListResponse(total=total, limit=limit, skip=skip, items=posts)


@router.get("/{id}", response_model=RawPostResponse, summary="Get Single Raw Post")
async def get_raw_post(id: str):
    """Retrieve detailed single raw post by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid RawPost ID format: '{id}'. Must be a valid 24-character hex string.",
        )

    db = get_database()
    raw_post_repo = RawPostRepository(db)
    post = await raw_post_repo.get_by_id(id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RawPost with ID '{id}' not found.",
        )
    return post
