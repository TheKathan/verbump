"""Load verbump.toml.

    tag_format = "{name}/v{version}"     # defaults for every package
    changelog = "CHANGELOG.md"            # relative to the package path

    [packages.api]
    path = "services/api"
    files = ["pyproject.toml", { path = "src/api/version.txt", pattern = '...(?P<version>...)' }]
    watch = ["libs/shared"]               # more repo paths whose changes release this package
    exclude = ["*.md", "docs/**"]         # changes here alone don't release it
"""

import posixpath
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from verbump.files import VersionFile, default_pattern

DEFAULT_TAG_FORMAT = "{name}/v{version}"
DEFAULT_COMMIT = "chore(release): {releases}"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PACKAGE_KEYS = {"path", "files", "watch", "exclude", "tag_format", "changelog", "major_tag", "initial_version"}
TOP_KEYS = {"tag_format", "changelog", "commit_message", "major_tag", "packages"}


class ConfigError(ValueError):
    pass


@dataclass
class Package:
    name: str
    path: str
    files: list[VersionFile]
    watch: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    tag_format: str = DEFAULT_TAG_FORMAT
    changelog: str | None = "CHANGELOG.md"
    major_tag: bool = False
    initial_version: str = "0.0.0"

    def repo_path(self, rel: str) -> str:
        return posixpath.normpath(posixpath.join(self.path, rel))

    @property
    def changelog_path(self) -> str | None:
        return self.repo_path(self.changelog) if self.changelog else None

    @property
    def paths(self) -> list[str]:
        return [self.path, *self.watch]

    def tag(self, version: str) -> str:
        return self.tag_format.format(name=self.name, version=version)

    def major_tag_name(self, version: str) -> str:
        return self.tag(version).rsplit(version, 1)[0] + version.split(".")[0]

    def tag_regex(self) -> re.Pattern:
        head, _, tail = self.tag_format.partition("{version}")
        return re.compile(
            "^" + re.escape(head.format(name=self.name)) + r"(?P<version>\d+\.\d+\.\d+)"
            + re.escape(tail.format(name=self.name)) + "$"
        )


@dataclass
class Config:
    packages: list[Package]
    commit_message: str = DEFAULT_COMMIT

    def get(self, name: str) -> Package:
        for p in self.packages:
            if p.name == name:
                return p
        raise ConfigError(f"no package named {name!r} (known: {', '.join(p.name for p in self.packages)})")


def load(path: Path) -> Config:
    if not path.is_file():
        raise ConfigError(f"{path}: not found (create a verbump.toml, see `verbump init`)")
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e
    return parse(data)


def parse(data: dict) -> Config:
    unknown = set(data) - TOP_KEYS
    if unknown:
        raise ConfigError(f"unknown top-level keys: {', '.join(sorted(unknown))}")
    raw = data.get("packages")
    if not isinstance(raw, dict) or not raw:
        raise ConfigError("no [packages.<name>] tables")
    defaults = {k: data[k] for k in ("tag_format", "changelog", "major_tag") if k in data}
    packages = [_package(name, {**defaults, **spec}) for name, spec in raw.items()]
    _check_unique_tags(packages)
    return Config(packages=packages, commit_message=data.get("commit_message", DEFAULT_COMMIT))


def _package(name: str, spec: dict) -> Package:
    if not NAME_RE.match(name):
        raise ConfigError(f"package name {name!r}: use letters, digits, '.', '_' or '-'")
    unknown = set(spec) - PACKAGE_KEYS
    if unknown:
        raise ConfigError(f"[packages.{name}]: unknown keys {', '.join(sorted(unknown))}")
    path = posixpath.normpath(spec.get("path", "."))
    if path.startswith(("..", "/")):
        raise ConfigError(f"[packages.{name}]: path must stay inside the repo")
    tag_format = spec.get("tag_format", DEFAULT_TAG_FORMAT)
    if tag_format.count("{version}") != 1:
        raise ConfigError(f"[packages.{name}]: tag_format needs exactly one {{version}}")
    files = []
    for f in spec.get("files", []):
        if isinstance(f, str):
            f = {"path": f}
        if not isinstance(f, dict) or "path" not in f:
            raise ConfigError(f"[packages.{name}]: each file is a path or {{ path, pattern }}")
        rel = posixpath.normpath(posixpath.join(path, f["path"]))
        try:
            files.append(VersionFile(rel, f.get("pattern") or default_pattern(rel)))
        except ValueError as e:
            raise ConfigError(f"[packages.{name}]: {e}") from e
    changelog = spec.get("changelog", "CHANGELOG.md")
    return Package(
        name=name,
        path=path,
        files=files,
        watch=[posixpath.normpath(w) for w in spec.get("watch", [])],
        exclude=list(spec.get("exclude", [])),
        tag_format=tag_format,
        changelog=changelog or None,
        major_tag=bool(spec.get("major_tag", False)),
        initial_version=spec.get("initial_version", "0.0.0"),
    )


def _check_unique_tags(packages: list[Package]) -> None:
    seen = {}
    for p in packages:
        probe = p.tag("1.2.3")
        if probe in seen:
            raise ConfigError(f"packages {seen[probe]!r} and {p.name!r} would share tags; give one its own tag_format")
        seen[probe] = p.name
