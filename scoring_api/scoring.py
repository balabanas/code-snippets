import hashlib
import json
import random


# def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
#     score = 0
#     if phone:
#         score += 1.5
#     if email:
#         score += 1.5
#     if birthday and gender:
#         score += 1.5
#     if first_name and last_name:
#         score += 0.5
#     return score
def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    print('store', store)
    key_parts = [
        first_name or "",
        last_name or "",
        phone or "",
        birthday.strftime("%Y%m%d") if birthday is not None else "",
    ]
    encoded_join_key_parts = "".join(map(str, key_parts)).encode('utf-8')
    key = "uid:" + hashlib.md5(encoded_join_key_parts).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    if score:
        return float(score)
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

# def get_interests(store, cid):
#     interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
#     return random.sample(interests, 2)
def get_interests(store, cid):
    print('request to redis: ', "i:%s" % cid)
    r = store.get("i:%s" % cid)
    print('got from store.get: ', r)
    return json.loads(r) if r else []
