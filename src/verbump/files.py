"""Read and write the version inside the files that carry it.

A file is matched by a regex with a named group `version`. Files of the common stacks get a
kind from their name, so most configs only list paths. Any file can name a `kind`, or set
its own `pattern`, optionally searched only `after` a marker and rewritten at every match.
"""

import re
from dataclasses import dataclass
from pathlib import Path

V = r"\d+\.\d+\.\d+"


@dataclass(frozen=True)
class Kind:
    pattern: str
    after: str | None = None
    replace_all: bool = False


KINDS = {
    "toml": Kind(rf'(?m)^version\s*=\s*"(?P<version>{V})"'),
    "json": Kind(rf'"version"\s*:\s*"(?P<version>{V})"'),
    "yaml": Kind(rf"(?m)^version:\s*['\"]?(?P<version>{V})"),
    "helm": Kind(rf"(?m)^(?:version|appVersion):\s*['\"]?v?(?P<version>{V})", replace_all=True),
    "plain": Kind(rf"\A\s*v?(?P<version>{V})"),
    "python": Kind(rf"__version__\s*=\s*['\"](?P<version>{V})['\"]"),
    "msbuild": Kind(rf"<(?:Version|VersionPrefix)>(?P<version>{V})</"),
    "assemblyinfo": Kind(rf'Assembly(?:File|Informational)?Version\(\s*"(?P<version>{V})', replace_all=True),
    "maven": Kind(rf"<version>(?P<version>{V})</version>", after="</parent>"),
    "properties": Kind(rf"(?m)^version\s*[=:]\s*(?P<version>{V})"),
    "gradle": Kind(rf"""(?m)^\s*version\s*=?\s*["'](?P<version>{V})["']"""),
    "ruby": Kind(rf"""(?:VERSION|\.version)\s*=\s*["'](?P<version>{V})["']"""),
    "elixir": Kind(rf'version:\s*"(?P<version>{V})"'),
    "dockerfile": Kind(rf"""(?im)^LABEL\s.*?version\s*=\s*["']?(?P<version>{V})"""),
}

BY_NAME = {
    "pyproject.toml": "toml",
    "Cargo.toml": "toml",
    "package.json": "json",
    "composer.json": "json",
    "deno.json": "json",
    "jsr.json": "json",
    "manifest.json": "json",
    "Chart.yaml": "yaml",
    "pubspec.yaml": "yaml",
    "VERSION": "plain",
    "VERSION.txt": "plain",
    "version.txt": "plain",
    ".version": "plain",
    "AssemblyInfo.cs": "assemblyinfo",
    "pom.xml": "maven",
    "gradle.properties": "properties",
    "setup.cfg": "properties",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "version.rb": "ruby",
    "mix.exs": "elixir",
    "Dockerfile": "dockerfile",
}
BY_SUFFIX = {
    ".py": "python",
    ".csproj": "msbuild",
    ".fsproj": "msbuild",
    ".vbproj": "msbuild",
    ".props": "msbuild",
    ".gemspec": "ruby",
}


class VersionFileError(ValueError):
    pass


@dataclass(frozen=True)
class VersionFile:
    path: str
    pattern: str
    after: str | None = None
    replace_all: bool = False

    def regex(self) -> re.Pattern:
        rx = re.compile(self.pattern)
        if "version" not in rx.groupindex:
            raise VersionFileError(f"{self.path}: pattern has no (?P<version>...) group")
        return rx

    def read(self, root: Path) -> str:
        text = self._text(root)
        return self._matches(text)[0].group("version")

    def write(self, root: Path, version: str) -> bool:
        text = self._text(root)
        matches = self._matches(text)
        if not self.replace_all:
            matches = matches[:1]
        new = text
        for m in reversed(matches):
            start, end = m.span("version")
            new = new[:start] + version + new[end:]
        if new == text:
            return False
        (root / self.path).write_text(new)
        return True

    def _matches(self, text: str) -> list[re.Match]:
        start = 0
        if self.after and (i := text.find(self.after)) >= 0:
            start = i + len(self.after)
        matches = list(self.regex().finditer(text, start))
        if not matches:
            raise VersionFileError(f"{self.path}: no version matches {self.pattern!r}")
        return matches

    def _text(self, root: Path) -> str:
        p = root / self.path
        if not p.is_file():
            raise VersionFileError(f"{self.path}: file not found")
        return p.read_text()


def kind_for(path: str) -> str:
    name, suffix = Path(path).name, Path(path).suffix
    if name in BY_NAME:
        return BY_NAME[name]
    if suffix in BY_SUFFIX:
        return BY_SUFFIX[suffix]
    raise VersionFileError(
        f"{path}: unknown file type; set `kind` (one of {', '.join(KINDS)}) or a `pattern` with a (?P<version>...) group"
    )


def version_file(path: str, kind: str | None = None, pattern: str | None = None, after: str | None = None,
                 replace_all: bool | None = None) -> VersionFile:
    """A version file from its config: an explicit pattern wins, then the kind, then the file name."""
    base = None
    if not pattern:
        name = kind or kind_for(path)
        if name not in KINDS:
            raise VersionFileError(f"{path}: unknown kind {name!r}; use one of {', '.join(KINDS)}")
        base = KINDS[name]
    return VersionFile(
        path=path,
        pattern=pattern or base.pattern,
        after=after if after is not None else (base.after if base else None),
        replace_all=replace_all if replace_all is not None else (base.replace_all if base else False),
    )
