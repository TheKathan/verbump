"""Read and write the version inside the files that carry it.

A file is matched by a regex with a named group `version`. Common files get a pattern from
their name, so most configs only list paths; anything else sets `pattern` itself.
"""

import re
from dataclasses import dataclass
from pathlib import Path

SEMVER_RE = r"\d+\.\d+\.\d+"

KNOWN = {
    "pyproject.toml": rf'(?m)^version\s*=\s*"(?P<version>{SEMVER_RE})"',
    "Cargo.toml": rf'(?m)^version\s*=\s*"(?P<version>{SEMVER_RE})"',
    "package.json": rf'"version"\s*:\s*"(?P<version>{SEMVER_RE})"',
    "Chart.yaml": rf"(?m)^version:\s*['\"]?(?P<version>{SEMVER_RE})",
    "VERSION": rf"\A\s*v?(?P<version>{SEMVER_RE})",
}
BY_SUFFIX = {
    ".py": rf"__version__\s*=\s*['\"](?P<version>{SEMVER_RE})['\"]",
    ".csproj": rf"<Version>(?P<version>{SEMVER_RE})</Version>",
    ".props": rf"<Version>(?P<version>{SEMVER_RE})</Version>",
}


class VersionFileError(ValueError):
    pass


@dataclass(frozen=True)
class VersionFile:
    path: str
    pattern: str

    def regex(self) -> re.Pattern:
        rx = re.compile(self.pattern)
        if "version" not in rx.groupindex:
            raise VersionFileError(f"{self.path}: pattern has no (?P<version>...) group")
        return rx

    def read(self, root: Path) -> str:
        text = self._text(root)
        m = self.regex().search(text)
        if not m:
            raise VersionFileError(f"{self.path}: no version matches {self.pattern!r}")
        return m.group("version")

    def write(self, root: Path, version: str) -> bool:
        text = self._text(root)
        rx = self.regex()
        m = rx.search(text)
        if not m:
            raise VersionFileError(f"{self.path}: no version matches {self.pattern!r}")
        start, end = m.span("version")
        new = text[:start] + version + text[end:]
        if new == text:
            return False
        (root / self.path).write_text(new)
        return True

    def _text(self, root: Path) -> str:
        p = root / self.path
        if not p.is_file():
            raise VersionFileError(f"{self.path}: file not found")
        return p.read_text()


def default_pattern(path: str) -> str:
    name = Path(path).name
    if name in KNOWN:
        return KNOWN[name]
    suffix = Path(path).suffix
    if suffix in BY_SUFFIX:
        return BY_SUFFIX[suffix]
    raise VersionFileError(f"{path}: no default pattern for this file; set `pattern` with a (?P<version>...) group")
