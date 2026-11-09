import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

MONOREPO_CONFIG = """\
tag_format = "{name}/v{version}"

[packages.api]
path = "services/api"
files = ["pyproject.toml", "src/api/__init__.py"]
watch = ["libs/shared"]
exclude = ["*.md"]

[packages.web]
path = "apps/web"
files = ["package.json"]
"""


def run(root: Path, *args: str) -> str:
    return subprocess.run(args, cwd=root, check=True, capture_output=True, text=True).stdout


class Repo:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        run(self.root, "git", "init", "-q", "-b", "main")
        run(self.root, "git", "config", "user.email", "test@example.com")
        run(self.root, "git", "config", "user.name", "Test")
        run(self.root, "git", "config", "commit.gpgsign", "false")
        run(self.root, "git", "config", "tag.gpgsign", "false")

    def write(self, path: str, text: str) -> None:
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text))

    def read(self, path: str) -> str:
        return (self.root / path).read_text()

    def commit(self, message: str) -> None:
        run(self.root, "git", "add", "-A")
        run(self.root, "git", "commit", "-q", "-m", message)

    def tag(self, name: str) -> None:
        run(self.root, "git", "tag", name)

    def cleanup(self) -> None:
        self._tmp.cleanup()


def monorepo() -> Repo:
    r = Repo()
    r.write("verbump.toml", MONOREPO_CONFIG)
    r.write("services/api/pyproject.toml", '[project]\nname = "api"\nversion = "1.4.0"\n')
    r.write("services/api/src/api/__init__.py", '__version__ = "1.4.0"\n')
    r.write("services/api/CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n### Added\n- Orders endpoint.\n")
    r.write("apps/web/package.json", json.dumps({"name": "web", "version": "0.3.0"}, indent=2) + "\n")
    r.write("libs/shared/util.py", "X = 1\n")
    r.commit("feat: initial import")
    return r
