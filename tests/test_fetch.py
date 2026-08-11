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
        original_cache = fetch.CACHE
        fetch.CACHE = tmp / "cache"
        try:
            source = self._source(tmp)
            manifest = {}
            self.assertEqual(fetch.process(source, manifest, live=False), "NEW")
            self.assertEqual(fetch.process(source, manifest, live=False), "UNCHANGED")
            (fetch.ROOT / source["sample"]).write_text("fact one, revised")
            self.assertEqual(fetch.process(source, manifest, live=False), "CHANGED")
            self.assertEqual(len(manifest), 1)  # never duplicates entries
        finally:
            fetch.CACHE = original_cache
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_sample_reports_error(self):
        source = {"id": "t2", "url": "https://example.com", "type": "official",
                  "sample": "does/not/exist.md"}
        self.assertTrue(fetch.process(source, {}, live=False).startswith("ERROR"))
    
    def test_empty_source_is_an_error(self):
        import tempfile, shutil
        tmp = Path(tempfile.mkdtemp(dir=fetch.ROOT / "state"))
        original_cache = fetch.CACHE
        fetch.CACHE = tmp / "cache"
        try:
            sample = tmp / "empty.md"
            sample.write_text("")
            source = {"id": "t3", "url": "https://example.com", "type": "official",
                      "sample": str(sample.relative_to(fetch.ROOT))}
            self.assertTrue(fetch.process(source, {}, live=False).startswith("ERROR"))
        finally:
            fetch.CACHE = original_cache
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sample_path_cannot_escape_root(self):
        import tempfile, shutil
        tmp = Path(tempfile.mkdtemp(dir=fetch.ROOT / "state"))
        original_cache = fetch.CACHE
        fetch.CACHE = tmp / "cache"
        try:
            source = {"id": "t4", "url": "https://example.com", "type": "official",
                      "sample": "../../../etc/passwd"}
            self.assertTrue(fetch.process(source, {}, live=False).startswith("ERROR"))
        finally:
            fetch.CACHE = original_cache
            shutil.rmtree(tmp, ignore_errors=True)

class TestSourceRegistry(unittest.TestCase):
    def test_duplicate_source_id_rejected(self):
        import tempfile, shutil
        tmp = Path(tempfile.mkdtemp())
        registry = tmp / "sources.yaml"
        registry.write_text(
            "sources:\n"
            "  - id: a\n    type: official\n"
            "    url: https://x.example\n    sample: s.md\n"
            "  - id: a\n    type: community\n"
            "    url: https://y.example\n    sample: t.md\n")
        original = fetch.SOURCES
        fetch.SOURCES = registry
        try:
            with self.assertRaises(ValueError):
                fetch.load_sources()
        finally:
            fetch.SOURCES = original
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
