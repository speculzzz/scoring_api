import hashlib
from datetime import datetime
from typing import Optional

from store import Store


def get_score(
        store: Store,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        birthday: Optional[datetime] = None,
        gender: Optional[int] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
) -> float:
    key = None

    if store:
        key_parts = [
            first_name or "",
            last_name or "",
            phone or "",
            birthday or "",
        ]
        key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()

        # Try to get from cache
        try:
            score = store.cache_get(key)
            if score is not None:
                return float(score)
        except Exception:
            # The issues with the memcache is uncritical to the function
            pass

    # Calculate score
    score = 0.0
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender is not None:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    if store:
        try:
            # Cache the score for 60 minutes
            store.cache_set(key, score, 60 * 60)
        except Exception:
            pass

    return score


def get_interests(store: Store, cid: int) -> list:
    data = store.get(f"i:{cid}")
    return data if data is not None else []
