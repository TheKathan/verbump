"""Work out which packages release and at what version, then write it."""

import datetime
import fnmatch
import posixpath
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from verbump import changelog, gitutil, semver
from verbump.config import Config, Package

RELEASE_BRANCH = re.compile(r"^release/(?:(?P<name>[^/]+)/)?v?(?P<version>\d+\.\d+\.\d+)$")


class ReleaseError(RuntimeError):
    pass


@dataclass
class State:
    package: Package
    file_version: str | None
    last_tag: str | None
    last_version: str | None
    changed: list[str]

    @property
    def current(self) -> str | None:
        known = [v for v in (self.file_version, self.last_version) if v]
        return max(known, key=semver.parse) if known else None


@dataclass
class Release:
    name: str
    path: str
    previous: str | None
    version: str
    tag: str
    major_tag: str | None
    changelog: str | None
    reason: str
    changed: list[str] = field(default_factory=list)


def last_release(root: Path, pkg: Package, tags: list[str]) -> tuple[str | None, str | None]:
    rx = pkg.tag_regex()
    found = [(semver.parse(m.group("version")), t, m.group("version")) for t in tags if (m := rx.match(t))]
    if not found:
        return None, None
    _, tag, version = max(found)
    return tag, version


def file_version(root: Path, pkg: Package) -> str | None:
    versions = {f.path: f.read(root) for f in pkg.files}
    if len(set(versions.values())) > 1:
        raise ReleaseError(f"{pkg.name}: version files disagree: {versions}")
    return next(iter(versions.values()), None)


def excluded(pkg: Package, path: str) -> bool:
    rel = posixpath.relpath(path, pkg.path) if pkg.path != "." else path
    return any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(rel, pat) for pat in pkg.exclude)


def state(root: Path, pkg: Package, tags: list[str]) -> State:
    tag, version = last_release(root, pkg, tags)
    files = gitutil.changed_files(root, tag, pkg.paths)
    return State(pkg, file_version(root, pkg), tag, version, [f for f in files if not excluded(pkg, f)])


def exact_from_branch(cfg: Config, branch: str | None) -> dict[str, str]:
    m = RELEASE_BRANCH.match(branch or "")
    if not m:
        return {}
    name = m.group("name")
    if name is None:
        if len(cfg.packages) != 1:
            raise ReleaseError(f"{branch}: name the package, e.g. release/<package>/{m.group('version')}")
        name = cfg.packages[0].name
    cfg.get(name)
    return {name: m.group("version")}


def plan(root: Path, cfg: Config, bump: str, exact: dict[str, str] | None = None,
         only: list[str] | None = None) -> list[Release]:
    exact = {k: semver.normalize(v) for k, v in (exact or {}).items()}
    for name in [*exact, *(only or [])]:
        cfg.get(name)
    tags = gitutil.tags_merged(root)
    releases = []
    for pkg in cfg.packages:
        if only and pkg.name not in only:
            continue
        st = state(root, pkg, tags)
        if pkg.name in exact:
            version, reason = exact[pkg.name], "exact"
            if st.last_version and semver.parse(version) <= semver.parse(st.last_version):
                raise ReleaseError(f"{pkg.name}: {version} is not newer than the last release {st.last_version}")
        elif not st.changed:
            continue
        elif st.last_tag is None and st.file_version:
            version, reason = st.file_version, "first release"
        elif st.last_tag is None:
            version, reason = semver.bump(pkg.initial_version, bump), "first release"
        else:
            version, reason = semver.bump(st.current, bump), bump
        tag = pkg.tag(version)
        if gitutil.tag_exists(root, tag):
            raise ReleaseError(f"{pkg.name}: tag {tag} already exists")
        releases.append(Release(
            name=pkg.name, path=pkg.path, previous=st.last_version, version=version, tag=tag,
            major_tag=pkg.major_tag_name(version) if pkg.major_tag else None,
            changelog=pkg.changelog_path, reason=reason, changed=st.changed,
        ))
    return releases


def apply(root: Path, cfg: Config, releases: list[Release], date: str | None = None) -> list[str]:
    """Write every release into its files and changelog; returns the paths it changed."""
    date = date or datetime.datetime.now(datetime.UTC).date().isoformat()
    tags = gitutil.tags_merged(root)
    touched = []
    for r in releases:
        pkg = cfg.get(r.name)
        for f in pkg.files:
            if f.write(root, r.version):
                touched.append(f.path)
        if pkg.changelog_path:
            last_tag, _ = last_release(root, pkg, tags)
            path = root / pkg.changelog_path
            old = path.read_text() if path.is_file() else None
            new = changelog.release(old, r.version, date, gitutil.log_subjects(root, last_tag, pkg.paths))
            if new != old:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(new)
                touched.append(pkg.changelog_path)
    return touched


def commit_message(cfg: Config, releases: list[Release]) -> str:
    return cfg.commit_message.format(releases=", ".join(f"{r.name} {r.version}" for r in releases))


def to_json(cfg: Config, bump: str, releases: list[Release]) -> dict:
    return {
        "bump": bump,
        "commit_message": commit_message(cfg, releases) if releases else "",
        "releases": [asdict(r) for r in releases],
    }
