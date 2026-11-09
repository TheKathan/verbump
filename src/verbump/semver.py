"""Plain X.Y.Z versions: parse, compare and bump."""

import re

SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
BUMPS = ("major", "minor", "patch")


class VersionError(ValueError):
    pass


def parse(text: str) -> tuple[int, int, int]:
    m = SEMVER.match(text.strip())
    if not m:
        raise VersionError(f"not an X.Y.Z version: {text!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def normalize(text: str) -> str:
    return ".".join(map(str, parse(text)))


def bump(version: str, kind: str) -> str:
    major, minor, patch = parse(version)
    kind = kind.lower()
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise VersionError(f"unknown bump {kind!r}; use one of {', '.join(BUMPS)}")


def bump_between(previous: str, new: str) -> str:
    """The bump that turns `previous` into `new`, e.g. trunk-semver's previous-version and version."""
    p, n = parse(previous), parse(new)
    if n <= p:
        raise VersionError(f"{new} is not newer than {previous}")
    if n[0] != p[0]:
        return "major"
    if n[1] != p[1]:
        return "minor"
    return "patch"


def bump_for_branch(branch: str) -> str:
    """trunk-semver's branch rule, for runs without it: feature/* and feat/* are minor, the rest patch."""
    return "minor" if branch.startswith(("feature/", "feat/")) else "patch"
