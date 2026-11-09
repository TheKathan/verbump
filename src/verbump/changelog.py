"""Keep a Changelog files: turn "Unreleased" into a version section, and read a section back.

The notes written under "## [Unreleased]" become the release. When nobody wrote any, the
section lists the commit subjects that touched the package since its last release.
"""

import re

HEADER = (
    "# Changelog\n\n"
    "All notable changes are listed here. The format follows "
    "[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow "
    "[Semantic Versioning](https://semver.org/).\n\n"
    "## [Unreleased]\n"
)
UNRELEASED = re.compile(r"^## \[Unreleased\][^\n]*\n", re.MULTILINE)
ANY_SECTION = re.compile(r"^## \[", re.MULTILINE)
SKIP_SUBJECT = re.compile(r"^(chore\(release\)|Merge )")


def section_re(version: str) -> re.Pattern:
    return re.compile(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", re.DOTALL | re.MULTILINE)


def commit_entries(commits: list[tuple[str, str]]) -> str:
    lines = [f"- {subject} ({sha})" for sha, subject in commits if not SKIP_SUBJECT.match(subject)]
    return "### Changes\n" + "\n".join(lines) + "\n" if lines else ""


def release(text: str | None, version: str, date: str, commits: list[tuple[str, str]]) -> str:
    """The changelog with a `## [version] - date` section; unchanged if that section exists."""
    text = text if text is not None else HEADER
    if section_re(version).search(text):
        return text
    m = UNRELEASED.search(text)
    if m:
        nxt = ANY_SECTION.search(text, m.end())
        body_end = nxt.start() if nxt else len(text)
        body = text[m.end():body_end].strip()
        head, rest = text[:m.end()], text[body_end:]
    else:
        nxt = ANY_SECTION.search(text)
        cut = nxt.start() if nxt else len(text)
        body = ""
        head, rest = text[:cut].rstrip("\n") + "\n\n## [Unreleased]\n", text[cut:]
    body = body or commit_entries(commits).strip() or "No notable changes."
    section = f"\n## [{version}] - {date}\n\n{body}\n"
    return head + section + ("\n" + rest if rest else "")


def notes(text: str, version: str) -> str:
    m = section_re(version).search(text or "")
    return (m.group(1).strip() if m else "") or f"Release {version}."
