"""Router utility helpers."""

from __future__ import annotations

from typing import Sequence, Tuple, TypeVar

from fastapi import Request

from metaqore.api.schemas import ResponseMetadata


def build_response_metadata(request: Request) -> ResponseMetadata:
    return ResponseMetadata(
        request_id=getattr(request.state, "request_id", "-"),
        latency_ms=float(getattr(request.state, "latency_ms", 0.0)),
    )


T = TypeVar("T")


def paginate_items(items: Sequence[T], page: int, page_size: int) -> Tuple[list[T], int]:
    total = len(items)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    if start >= total:
        return [], total
    return list(items[start:end]), total
