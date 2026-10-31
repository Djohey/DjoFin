"""Free-only RSS/Atom polling: provenance-first, no AI calls or trading.

Usage: python scripts/collect_public_feeds.py --output data/news/news.jsonl
No scheduled execution is configured by this script.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = {
    "ecb_press": "https://www.ecb.europa.eu/rss/press.html",
    "sec_press": "https://www.sec.gov/news/pressreleases.rss",
}
MAX_BYTES = 2_000_000

def text(node, names):
    for name in names:
        value = node.find(name)
        if value is not None and value.text:
            return unescape(value.text.strip())
    return ""

def parse_feed(payload, feed_id, fetched_at):
    root = ET.fromstring(payload)
    entries = root.findall(".//item")
    atom = False
    if not entries:
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        atom = True
    results = []
    for entry in entries:
        title = text(entry, ["title", "{http://www.w3.org/2005/Atom}title"])
        link = text(entry, ["link"])
        if atom:
            for el in entry.findall("{http://www.w3.org/2005/Atom}link"):
                if el.attrib.get("rel", "alternate") == "alternate" and el.attrib.get("href"):
                    link = el.attrib["href"]
                    break
        published = text(entry, ["pubDate", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"])
        if not title or not link.startswith("https://"):
            continue
        fingerprint = sha256((feed_id+"\n"+link+"\n"+title+"\n"+published).encode()).hexdigest()
        results.append({"id": fingerprint, "feed_id": feed_id, "title": title, "url": link, "published_raw": published or None, "fetched_utc": fetched_at, "publication_time_verified": False, "source_type": "official_feed", "verification_status": "unverified"})
    return results

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "DjoFinResearch/0.1 (public RSS research; contact via repository)", "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Feed exceeds maximum size")
        return data

def collect(feeds=FEEDS, fetcher=fetch):
    fetched_at = datetime.now(timezone.utc).isoformat()
    entries, errors = [], []
    for feed_id, url in feeds.items():
        try:
            entries.extend(parse_feed(fetcher(url), feed_id, fetched_at))
        except (OSError, ValueError, ET.ParseError) as exc:
            errors.append({"feed_id": feed_id, "error_type": type(exc).__name__, "message": str(exc)[:180]})
    return entries, errors

def save(entries, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    seen.add(json.loads(line)["id"])
                except (ValueError, KeyError):
                    continue
    new = [item for item in entries if item["id"] not in seen]
    with path.open("a", encoding="utf-8") as handle:
        for item in new:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True)+"\n")
    return len(new)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/news/news.jsonl")
    args = parser.parse_args()
    entries, errors = collect()
    print(json.dumps({"fetched": len(entries), "new": save(entries, args.output), "errors": errors}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
