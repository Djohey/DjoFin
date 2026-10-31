"""Offline regression tests for the EXACT production market writer (no network)."""
import base64
import hashlib
import io
import json
import os
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import djofin_trusted_writers as w

class Response(io.BytesIO):
    status=201
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

class MarketTests(unittest.TestCase):
    def setUp(self):
        self.saved=None
        self.calls=[]
        self.env=patch.dict(os.environ,{"GH_REPOSITORY":"Djohey/DjoFin","GH_TOKEN":"test-token"})
        self.env.start()
    def tearDown(self):self.env.stop()
    def fake(self,request,timeout=20):
        url=request.full_url
        self.calls.append((request.get_method(),url))
        if "finance.yahoo.com" in url:
            days=[1761000000+i*86400 for i in range(10)]
            chart={"chart":{"result":[{"meta":{"symbol":"CW8.PA","currency":"EUR"},
                 "timestamp":days,"indicators":{"quote":[{"open":[700.0]*10,"close":[701.0]*10}]}}]}}
            return Response(json.dumps(chart).encode())
        if request.get_method()=="PUT":
            self.saved=json.loads(request.data)
            return Response(b'{}')
        if self.saved:
            payload=base64.b64decode(self.saved["content"])
            return Response(json.dumps({"encoding":"base64","content":base64.b64encode(payload).decode()}).encode())
        raise urllib.error.HTTPError(url,404,"not found",{},None)
    def test_writes_valid_json_and_sha(self):
        with patch.object(urllib.request,"urlopen",self.fake):w.market()
        obj=json.loads(base64.b64decode(self.saved["content"]))
        data=base64.b64decode(obj["csv_base64"])
        self.assertEqual(hashlib.sha256(data).hexdigest(),obj["metadata"]["csv_sha256"])
        self.assertTrue(base64.b64decode(self.saved["content"]).endswith(b"}\n"))
    def test_second_run_does_not_overwrite(self):
        with patch.object(urllib.request,"urlopen",self.fake):
            w.market()
            w.market()
        self.assertEqual(sum(method=="PUT" for method,url in self.calls),1)
    def test_corrupt_existing_snapshot_fails_closed(self):
        self.saved={"content":base64.b64encode(b'{"bad":true}\n').decode()}
        with patch.object(urllib.request,"urlopen",self.fake):
            with self.assertRaises((KeyError,ValueError)):w.market()
        self.assertFalse(any(method=="PUT" for method,url in self.calls))
if __name__=="__main__":unittest.main()
