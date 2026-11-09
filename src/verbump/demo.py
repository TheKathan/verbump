"""`verbump demo`: a narrated release in a throwaway repo with a Python and a Node package."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

CONFIG = """\
[packages.api]
path = "services/api"
files = ["pyproject.toml"]

[packages.web]
path = "apps/web"
files = ["package.json"]
"""

GIT = ["git", "-c", "user.name=demo", "-c", "user.email=demo@example.com", "-c", "commit.gpgsign=false",
       "-c", "tag.gpgsign=false", "-c", "init.defaultBranch=main"]


def git(root: Path, *args: str) -> str:
    return subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True, text=True).stdout


def write(root: Path, path: str, text: str) -> None:
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def changelog(*sections: str) -> str:
    return "# Changelog\n\n## [Unreleased]\n" + "".join(sections)


def setup(root: Path) -> None:
    """Build the demo repo: api 1.4.0 and web 0.3.0 released, then a PR that changed web."""
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q")
    write(root, "verbump.toml", CONFIG)
    write(root, "services/api/pyproject.toml", '[project]\nname = "api"\nversion = "1.4.0"\n')
    write(root, "services/api/app.py", "def health():\n    return 'ok'\n")
    write(root, "services/api/CHANGELOG.md", changelog("\n## [1.4.0] - 2026-11-02\n\n- Health check.\n"))
    write(root, "apps/web/package.json", json.dumps({"name": "web", "version": "0.3.0"}, indent=2) + "\n")
    write(root, "apps/web/index.js", "export const home = () => 'home'\n")
    write(root, "apps/web/CHANGELOG.md", changelog("\n## [0.3.0] - 2026-11-02\n\n- Home page.\n"))
    git(root, "add", "-A")
    git(root, "commit", "-qm", "chore(release): api 1.4.0, web 0.3.0")
    git(root, "tag", "api/v1.4.0")
    git(root, "tag", "web/v0.3.0")
    write(root, "apps/web/checkout.js", "export const checkout = () => 'pay'\n")
    write(root, "apps/web/CHANGELOG.md", changelog("\n### Added\n- Checkout page.\n",
                                                   "\n## [0.3.0] - 2026-11-02\n\n- Home page.\n"))
    git(root, "add", "-A")
    git(root, "commit", "-qm", "feat(web): checkout page")


def run(root: Path, *args: str) -> None:
    print(f"$ {' '.join(args)}", flush=True)
    cmd = [sys.executable, "-m", "verbump", *args[1:]] if args[0] == "verbump" else [*GIT, *args[1:]]
    pkg_root = str(Path(__file__).resolve().parent.parent)
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [pkg_root, os.environ.get("PYTHONPATH")]))}
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False, env=env)
    out = (proc.stdout + proc.stderr).rstrip()
    if out:
        print(out)
    print()


def say(text: str) -> None:
    print(textwrap.fill(f"# {text}", width=88, subsequent_indent="# "))


def main(keep: Path | None = None, setup_only: bool = False) -> int:
    root = keep or Path(tempfile.mkdtemp(prefix="verbump-demo-"))
    if keep and keep.exists() and any(keep.iterdir()):
        raise ValueError(f"{keep} is not empty")
    setup(root)
    if setup_only:
        print(root)
        return 0
    try:
        say("A repo with two packages: api (Python) at 1.4.0 and web (Node) at 0.3.0, both tagged.")
        say("A PR from feat/checkout just changed apps/web and wrote a note under Unreleased.")
        print()
        run(root, "verbump", "status")
        say("feat/* is a minor bump. Only web changed since its tag, so only web moves.")
        run(root, "verbump", "plan", "--branch", "feat/checkout")
        run(root, "verbump", "apply", "--branch", "feat/checkout", "--date", "2026-11-09")
        say("The version and the changelog, written:")
        run(root, "git", "diff", "--stat")
        run(root, "verbump", "notes", "web")
        say("CI then commits, runs `verbump tag`, pushes, and uses those notes as the GitHub release.")
    finally:
        if keep is None:
            shutil.rmtree(root, ignore_errors=True)
    return 0
