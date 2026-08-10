"""Idempotency tests for the fetch layer. Run: python3 -m unittest discover tests"""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch


class TestNormalize(unittest.TestCase):
    def test_html_strips_chrome(self):
        html = ("<html><head><style>.x{}</style></head><body><nav>menu</nav>"
                "<p>Real   content</p><footer>legal</footer></body></html>")
        text = fetch.normalize(html, is_html=True)
        self.assertIn("Real content", text)
        self.assertNotIn("menu", text)
        self.assertNotIn("legal", text)
        self.assertNotIn(".x{}", text)

    def test_normalize_is_stable(self):
        raw = "a  b\n\n\n\nc\t d"
        once = fetch.normalize(raw, is_html=False)
        twice = fetch.normalize(once, is_html=False)
        self.assertEqual(once, twice)

    def test_whitespace_changes_do_not_change_hash(self):
        a = fetch.normalize("<p>Same  fact here</p>", is_html=True)
        b = fetch.normalize("<p>Same fact   here</p>", is_html=True)
        self.assertEqual(hashlib.sha256(a.encode()).hexdigest(),
                         hashlib.sha256(b.encode()).hexdigest())


class TestChangeDetection(unittest.TestCase):
    def _source(self, tmp_path):
        sample = tmp_path / "s.md"
        sample.write_text("fact one")
        return {"id": "t1", "url": "https://example.com", "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT)) else str(sample)}

    def test_new_then_unchanged_then_changed(self):
        import tempfile
        tmp = Path(tempfile.mkdtemp(dir=fetch.ROOT / "state"))
        try:
            source = self._source(tmp)
            manifest = {}
            self.assertEqual(fetch.process(source, manifest, live=False), "NEW")
            self.assertEqual(fetch.process(source, manifest, live=False), "UNCHANGED")
            (fetch.ROOT / source["sample"]).write_text("fact one, revised")
            self.assertEqual(fetch.process(source, manifest, live=False), "CHANGED")
            self.assertEqual(len(manifest), 1)  # never duplicates entries
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_sample_reports_error(self):
        source = {"id": "t2", "url": "https://example.com", "type": "official",
                  "sample": "does/not/exist.md"}
        self.assertTrue(fetch.process(source, {}, live=False).startswith("ERROR"))


if __name__ == "__main__":
    unittest.main()
