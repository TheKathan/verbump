import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from verbump import config, demo, release


class DemoTest(unittest.TestCase):
    def test_setup_plans_only_web(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            demo.setup(root)
            cfg = config.load(root / "verbump.toml")
            plan = release.plan(root, cfg, "minor")
            self.assertEqual([(r.name, r.version) for r in plan], [("web", "0.4.0")])

    def test_narrated_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            with redirect_stdout(out):
                demo.main(keep=Path(tmp) / "repo")
            text = out.getvalue()
            self.assertIn("web: 0.3.0 -> 0.4.0 (minor, tag web/v0.4.0)", text)
            self.assertIn("### Added\n- Checkout page.", text)
            self.assertIn('"version": "0.4.0"', (Path(tmp) / "repo/apps/web/package.json").read_text())

    def test_refuses_a_non_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x").write_text("1")
            with self.assertRaises(ValueError):
                demo.main(keep=Path(tmp))


if __name__ == "__main__":
    unittest.main()
