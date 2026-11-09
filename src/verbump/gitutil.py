"""Thin wrappers around the git commands verbump needs."""

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def tags_merged(root: Path) -> list[str]:
    return git(root, "tag", "--merged", "HEAD").split()


def tag_exists(root: Path, tag: str) -> bool:
    return bool(git(root, "tag", "--list", tag).strip())


def changed_files(root: Path, base: str | None, paths: list[str]) -> list[str]:
    """Files changed under `paths` since `base`; every tracked file under them when there is no base."""
    if base is None:
        out = git(root, "ls-files", "--", *paths)
    else:
        out = git(root, "diff", "--name-only", f"{base}..HEAD", "--", *paths)
    return [line for line in out.splitlines() if line]


def log_subjects(root: Path, base: str | None, paths: list[str]) -> list[tuple[str, str]]:
    """(short sha, subject) of the commits touching `paths` since `base`, oldest first."""
    rng = [f"{base}..HEAD"] if base else ["HEAD"]
    out = git(root, "log", "--reverse", "--no-merges", "--format=%h%x09%s", *rng, "--", *paths)
    return [tuple(line.split("\t", 1)) for line in out.splitlines() if "\t" in line]
