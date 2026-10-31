"""Trusted production collectors. Standard library only; no pip. Reviewed on main."""
def market():
    import base64,csv,hashlib,io,json,os,urllib.request,urllib.error
    from datetime import datetime,timezone
    repo=os.environ["GH_REPOSITORY"]
    assert repo=="Djohey/DjoFin"
    token=os.environ["GH_TOKEN"]
    today=datetime.now(timezone.utc).date().isoformat()
    root=f"data/market_archive_trusted/CW8_PA/{today}"
    url="https://query1.finance.yahoo.com/v8/finance/chart/CW8.PA?range=1mo&interval=1d"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 DjoFinHistoricalArchive/1"})
    with urllib.request.urlopen(req,timeout=20) as response:
        data=response.read(1_000_001)
    assert len(data)<=1_000_000,"Market response too large"
    result=json.loads(data)["chart"]["result"][0]
    assert result["meta"]["symbol"]=="CW8.PA"
    assert result["meta"]["currency"]=="EUR"
    quote=result["indicators"]["quote"][0]
    timestamps=result["timestamp"]
    rows=[]
    for ts,opening,closing in zip(timestamps,quote["open"],quote["close"]):
        day=datetime.fromtimestamp(ts,timezone.utc).date().isoformat()
        if opening is None or closing is None:continue
        opening=float(opening);closing=float(closing)
        if not (0<opening<100000 and 0<closing<100000):continue
        rows.append((day,format(opening,".12g"),format(closing,".12g")))
    assert 5<=len(rows)<=35,"Incomplete or unexpected price history"
    assert rows==sorted(rows),"Unordered dates"
    out=io.StringIO()
    writer=csv.writer(out,lineterminator="\n")
    writer.writerow(["Date","Open","Close"])
    writer.writerows(rows)
    csv_bytes=out.getvalue().encode()
    digest=hashlib.sha256(csv_bytes).hexdigest()
    meta={"ticker":"CW8.PA","currency":"EUR","source":"Yahoo Finance chart API, raw OHLC",
          "captured_utc":datetime.now(timezone.utc).isoformat(),"csv_sha256":digest,
          "observation_count":len(rows),"warning":"Modern vendor reconstruction, not point-in-time"}
    headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28","User-Agent":"DjoFinTrustedMarket/1",
             "Content-Type":"application/json"}
    # One atomic JSON blob prevents partial daily snapshots.
    archive={"metadata":meta,"csv_base64":base64.b64encode(csv_bytes).decode()}
    path=root+".json"
    endpoint=f"https://api.github.com/repos/{repo}/contents/{path}"
    try:
        check=urllib.request.Request(endpoint+"?ref=simulation-p0",headers=headers)
        with urllib.request.urlopen(check,timeout=20) as response:
            existing=json.load(response)
        if existing.get("encoding")!="base64": raise ValueError("Existing snapshot not readable")
        stored=json.loads(base64.b64decode(existing["content"]).decode().removesuffix("\\n"))
        saved=base64.b64decode(stored["csv_base64"])
        if hashlib.sha256(saved).hexdigest()!=stored["metadata"]["csv_sha256"]: raise ValueError("Stored snapshot hash mismatch")
        print(json.dumps({"status":"already_archived","date":today}))
        return
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    content=(json.dumps(archive,sort_keys=True)+"\n").encode()
    payload={"message":"data: immutable trusted CW8 daily OHLC archive",
             "branch":"simulation-p0","content":base64.b64encode(content).decode()}
    req=urllib.request.Request(endpoint,headers=headers,data=json.dumps(payload).encode(),method="PUT")
    with urllib.request.urlopen(req,timeout=25) as response:
        assert response.status==201
    print(json.dumps({"captured":today,"rows":len(rows),"sha256":digest}))

def news():
    import base64, hashlib, json, os, urllib.request, urllib.error
    import xml.etree.ElementTree as ET
    from datetime import datetime, timezone
    from html import unescape
    repo=os.environ["GH_REPOSITORY"]
    assert repo=="Djohey/DjoFin"
    token=os.environ["GH_TOKEN"]
    path="data/news/news.jsonl"
    url=f"https://api.github.com/repos/{repo}/contents/{path}"
    headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28","User-Agent":"DjoFinTrustedRSS/1"}
    def api(method="GET",payload=None):
        body=None if payload is None else json.dumps(payload).encode()
        h=dict(headers)
        if body is not None:h["Content-Type"]="application/json"
        req=urllib.request.Request(url,headers=h,data=body,method=method)
        with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
    previous={}
    sha=None
    try:
        read_url=url+"?ref=simulation-p0"
        request=urllib.request.Request(read_url,headers=headers)
        with urllib.request.urlopen(request,timeout=25) as response: obj=json.load(response)
        sha=obj["sha"]
        assert obj.get("encoding")=="base64" and isinstance(obj.get("content"),str), "GitHub omitted archive content: abort without writing"
        assert isinstance(obj.get("size"),int) and obj["size"]<900_000, "Archive approaching GitHub Contents API limit: rotate before writing"
        raw=base64.b64decode(obj["content"],validate=True)
        assert len(raw)==obj["size"], "Truncated GitHub archive: abort without writing"
        for line in raw.splitlines():
            if line.strip():
                row=json.loads(line)
                assert isinstance(row.get("id"),str) and len(row["id"])==64
                previous[row["id"]]=row
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    now=datetime.now(timezone.utc).isoformat()
    feeds={"ecb_press":"https://www.ecb.europa.eu/rss/press.html",
           "sec_press":"https://www.sec.gov/news/pressreleases.rss"}
    added=0
    for feed_id,feed_url in feeds.items():
        req=urllib.request.Request(feed_url,headers={"User-Agent":"DjoFinResearch/0.1 public RSS research",
                                                     "Accept":"application/rss+xml, application/xml, text/xml"})
        with urllib.request.urlopen(req,timeout=15) as response:
            data=response.read(2_000_001)
        assert len(data)<=2_000_000,"Feed too large"
        root=ET.fromstring(data)
        entries=root.findall(".//item")
        assert entries,"Missing RSS items: fail closed"
        for entry in entries:
            def field(name):
                node=entry.find(name)
                return unescape((node.text or "").strip()) if node is not None else ""
            title,link,published=field("title"),field("link"),field("pubDate")
            if not title or len(title)>2000 or not link.startswith("https://"):continue
            ident=hashlib.sha256((feed_id+"\n"+link+"\n"+title+"\n"+published).encode()).hexdigest()
            if ident in previous:continue
            previous[ident]={"id":ident,"feed_id":feed_id,"title":title,"url":link,
                "published_raw":published or None,"fetched_utc":now,
                "publication_time_verified":False,"source_type":"official_feed",
                "verification_status":"unverified"}
            added+=1
    if added:
        content="".join(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n" for row in previous.values())
        assert len(content.encode())<900_000,"News archive nearing API limit: rotate before writing"
        payload={"message":"data: append verified-source RSS records (unverified claims)",
                 "content":base64.b64encode(content.encode()).decode(),"branch":"simulation-p0"}
        # A write token is needed ONLY for this fixed-path contents operation.
        # No checkout or untrusted repository code executes in this job.
        if sha:payload["sha"]=sha
        req=urllib.request.Request(url,headers={**headers,"Content-Type":"application/json"},
                                   data=json.dumps(payload).encode(),method="PUT")
        with urllib.request.urlopen(req,timeout=30) as response:
            assert response.status in (200,201)
    print(json.dumps({"feeds":list(feeds),"new":added,"stored_total":len(previous)}))

if __name__=="__main__":
    import sys
    if len(sys.argv)!=2 or sys.argv[1] not in ("market","news"):raise SystemExit("usage: market|news")
    globals()[sys.argv[1]]()
