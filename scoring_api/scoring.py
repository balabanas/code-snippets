import hashlib
import json
import logging


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    """Uses store as cache if available. If not - still works"""
    key_parts = [
        first_name or "",
        last_name or "",
        phone or "",
        birthday.strftime("%Y%m%d") if birthday is not None else "",
    ]
    encoded_join_key_parts = "".join(map(str, key_parts)).encode('utf-8')
    key = "uid:" + hashlib.md5(encoded_join_key_parts).hexdigest()
    # try get from cache, fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    if score:
        return float(score)
    logging.info("get_score: Unable to find cached value, fallback to heavy calculations")
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def get_interests(store, cid):
    """Heavily rely on store (function .get will return TimeoutError if cache is not available)"""
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
