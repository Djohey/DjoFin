"""Trusted inline-workflow data writer helpers; NO external packages.

Production workflows must NOT import this file with a write token.
This module exists for unit tests and documentation of strict validation.
"""
import hashlib
import json
import re

def validate_rss_lines(data):
    if len(data)>2_000_000:
        raise ValueError("RSS data too large")
    out={}
    for line in data.splitlines():
        if not line.strip():
            continue
        item=json.loads(line)
        if not isinstance(item,dict) or not isinstance(item.get("id"),str) or not re.fullmatch(r"[0-9a-f]{64}",item["id"]):
            raise ValueError("Invalid news id")
        if item.get("feed_id") not in ("ecb_press","sec_press"):
            raise ValueError("Unexpected feed")
        if not isinstance(item.get("title"),str) or not (1<=len(item["title"])<=2000):
            raise ValueError("Invalid title")
        if not isinstance(item.get("url"),str) or not item["url"].startswith("https://"):
            raise ValueError("Invalid URL")
        out[item["id"]]=item
    return out

def merge_rss(existing,new):
    a=validate_rss_lines(existing)
    b=validate_rss_lines(new)
    a.update({k:v for k,v in b.items() if k not in a})
    return ("".join(json.dumps(v,ensure_ascii=False,sort_keys=True)+"\n" for v in a.values())).encode("utf-8")

def validate_market_snapshot(csv_bytes,meta_bytes):
    if len(csv_bytes)>1_000_000 or len(meta_bytes)>10_000:
        raise ValueError("Oversize market snapshot")
    meta=json.loads(meta_bytes)
    if meta.get("ticker")!="CW8.PA" or meta.get("csv_sha256")!=hashlib.sha256(csv_bytes).hexdigest():
        raise ValueError("Invalid market metadata or hash")
    return True
