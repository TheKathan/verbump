import json
import subprocess
import sys
import unittest
from pathlib import Path

from helpers import monorepo, run

from verbump import config, release

ROOT = Path(__file__).resolve().parent.parent


def cli(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "verbump", "-C", str(root), *args], capture_output=True, text=True,
                          check=check, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"})


class MonorepoTest(unittest.TestCase):
    def setUp(self):
        self.repo = monorepo()
        self.root = self.repo.root
        self.cfg = config.load(self.root / "verbump.toml")

    def tearDown(self):
        self.repo.cleanup()

    def release_all(self, bump="patch", **kw):
        releases = release.plan(self.root, self.cfg, bump, **kw)
        release.apply(self.root, self.cfg, releases, "2026-11-09")
        self.repo.commit(release.commit_message(self.cfg, releases))
        for r in releases:
            self.repo.tag(r.tag)
        return {r.name: r.version for r in releases}

    def test_first_release_keeps_the_file_versions(self):
        self.assertEqual(self.release_all(), {"api": "1.4.0", "web": "0.3.0"})
        log = self.repo.read("services/api/CHANGELOG.md")
        self.assertIn("## [1.4.0] - 2026-11-09\n\n### Added\n- Orders endpoint.", log)
        self.assertIn("## [0.3.0] - 2026-11-09\n\n### Changes\n- feat: initial import", self.repo.read("apps/web/CHANGELOG.md"))
        self.assertEqual(release.plan(self.root, self.cfg, "patch"), [])

    def test_only_the_changed_service_bumps(self):
        self.release_all()
        self.repo.write("apps/web/index.js", "console.log(1)\n")
        self.repo.commit("feat: web page")
        self.assertEqual(self.release_all("minor"), {"web": "0.4.0"})
        self.assertIn('"version": "0.4.0"', self.repo.read("apps/web/package.json"))
        self.assertIn('version = "1.4.0"', self.repo.read("services/api/pyproject.toml"))
        notes = cli(self.root, "notes", "web").stdout.strip()
        self.assertEqual(notes, "### Changes\n- feat: web page (" + run(self.root, "git", "rev-parse", "--short", "HEAD~1").strip() + ")")

    def test_watched_path_releases_and_exclude_does_not(self):
        self.release_all()
        self.repo.write("services/api/README.md", "docs\n")
        self.repo.commit("docs: readme")
        self.assertEqual(release.plan(self.root, self.cfg, "patch"), [])
        self.repo.write("libs/shared/util.py", "X = 2\n")
        self.repo.commit("fix: shared util")
        self.assertEqual(self.release_all(), {"api": "1.4.1"})
        self.assertEqual(self.repo.read("services/api/src/api/__init__.py"), '__version__ = "1.4.1"\n')

    def test_exact_release_branch(self):
        self.release_all()
        exact = release.exact_from_branch(self.cfg, "release/api/2.0.0")
        self.assertEqual(self.release_all(exact=exact), {"api": "2.0.0"})
        with self.assertRaises(release.ReleaseError):
            release.exact_from_branch(self.cfg, "release/3.0.0")
        with self.assertRaises(release.ReleaseError):
            release.plan(self.root, self.cfg, "patch", exact={"api": "1.0.0"})

    def test_existing_tag_fails(self):
        run(self.root, "git", "checkout", "-q", "-b", "side")
        self.repo.write("apps/web/x.js", "1\n")
        self.repo.commit("fix: x")
        self.repo.tag("web/v0.3.0")
        run(self.root, "git", "checkout", "-q", "main")
        with self.assertRaisesRegex(release.ReleaseError, "web/v0.3.0 already exists"):
            release.plan(self.root, self.cfg, "patch")

    def test_disagreeing_files_fail(self):
        self.repo.write("services/api/src/api/__init__.py", '__version__ = "9.9.9"\n')
        with self.assertRaisesRegex(release.ReleaseError, "disagree"):
            release.plan(self.root, self.cfg, "patch")
        self.assertEqual(cli(self.root, "check", check=False).returncode, 1)

    def test_cli_apply_tag_and_trunk_semver_inputs(self):
        self.release_all()
        self.repo.write("services/api/app.py", "1\n")
        self.repo.commit("feat: api thing")
        out = cli(self.root, "apply", "--previous", "v1.0.0", "--version-from", "v1.1.0", "--json",
                  "--plan-out", str(self.root / "plan.json"), "--date", "2026-11-09")
        data = json.loads(out.stdout)
        self.assertEqual(data["bump"], "minor")
        self.assertEqual([(r["name"], r["version"], r["tag"]) for r in data["releases"]], [("api", "1.5.0", "api/v1.5.0")])
        self.assertEqual(data["commit_message"], "chore(release): api 1.5.0")
        (self.root / "plan.json").rename(self.root.parent / f"{self.root.name}-plan.json")
        self.repo.commit(data["commit_message"])
        self.assertEqual(cli(self.root, "tag", "--plan", str(self.root.parent / f"{self.root.name}-plan.json")).stdout, "api/v1.5.0\n")
        self.assertIn("api/v1.5.0", run(self.root, "git", "tag", "--points-at", "HEAD"))
        self.assertEqual(cli(self.root, "plan").stdout, "nothing to release\n")
        status = json.loads(cli(self.root, "status", "--json").stdout)
        self.assertEqual({s["name"]: s["last_tag"] for s in status}, {"api": "api/v1.5.0", "web": "web/v0.3.0"})


if __name__ == "__main__":
    unittest.main()
