"""Regression tests of actual production RSS collector, with no network."""
import base64, io, json, os, sys, unittest, urllib.error, urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import djofin_trusted_writers as writer

class Response(io.BytesIO):
    status=201
    def __enter__(self):return self
    def __exit__(self,*a):self.close()

class NewsTests(unittest.TestCase):
    def setUp(self):
        self.saved=None
        self.requests=[]
        self.env=patch.dict(os.environ,{"GH_REPOSITORY":"Djohey/DjoFin","GH_TOKEN":"fake"})
        self.env.start()
    def tearDown(self):self.env.stop()
    def fake(self,request,timeout=25):
        url=request.full_url
        self.requests.append((request.get_method(),url))
        if "ecb.europa.eu" in url:
            return Response(b'<rss><channel><item><title>Rate decision</title><link>https://www.ecb.europa.eu/example</link><pubDate>today</pubDate></item></channel></rss>')
        if "sec.gov" in url:
            raise urllib.error.HTTPError(url,503,"Unavailable",{},None)
        if request.get_method()=="PUT":
            self.saved=json.loads(request.data)
            return Response(b'{}')
        if self.saved is None:
            raise urllib.error.HTTPError(url,404,"Missing",{},None)
        data=base64.b64decode(self.saved["content"])
        return Response(json.dumps({"sha":"fake-sha","encoding":"base64","size":len(data),"content":base64.b64encode(data).decode()}).encode())
    def test_partial_outage_preserves_successful_feed_and_signals_failure(self):
        with patch.object(urllib.request,"urlopen",self.fake):
            with self.assertRaises(SystemExit):writer.news()
        self.assertIsNotNone(self.saved)
        lines=base64.b64decode(self.saved["content"]).decode().splitlines()
        self.assertEqual(len(lines),1)
        self.assertEqual(json.loads(lines[0])["feed_id"],"ecb_press")
    def test_bad_existing_content_aborts_before_write(self):
        def bad(request,timeout=25):
            if "?ref=simulation-p0" in request.full_url:
                return Response(json.dumps({"sha":"fake","encoding":"none","size":10,"content":""}).encode())
            raise AssertionError("Unexpected request")
        with patch.object(urllib.request,"urlopen",bad):
            with self.assertRaises(AssertionError):writer.news()
        self.assertIsNone(self.saved)
if __name__=="__main__":unittest.main()
