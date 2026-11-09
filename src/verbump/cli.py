"""verbump command line.

  verbump status                               packages, versions, last tags, pending changes
  verbump plan  --previous v1.4.0 --version-from v1.5.0   what would release (trunk-semver outputs)
  verbump apply --bump minor --plan-out plan.json      write versions and changelogs
  verbump tag   --plan plan.json               create the planned git tags
  verbump notes <package> [<version>]          a version's changelog section, for a release body
  verbump set   <package> <version>            write an exact version into one package
  verbump check                                exit 1 if a package's version files disagree
  verbump init                                 write a starter verbump.toml
  verbump demo                                 a narrated release in a throwaway repo
"""

import argparse
import json
import sys
from pathlib import Path

from verbump import __version__, changelog, gitutil, release, semver
from verbump.config import Config, ConfigError, load

STARTER = '''\
# verbump: one table per package that has its own version.
# Tags are "<name>/v<version>" unless tag_format says otherwise.
tag_format = "{name}/v{version}"
changelog = "CHANGELOG.md"

[packages.app]
path = "."
files = ["pyproject.toml"]
# watch = ["libs/shared"]        # changes here also release this package
# exclude = ["*.md", "docs/*"]   # changes only here don't
'''


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    try:
        code = args.func(args)
    except (ConfigError, release.ReleaseError, semver.VersionError, gitutil.GitError, ValueError) as e:
        sys.exit(f"verbump: {e}")
    sys.exit(code or 0)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="verbump", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"verbump {__version__}")
    p.add_argument("-C", "--root", type=Path, default=Path("."), help="repo root (default: .)")
    p.add_argument("-c", "--config", type=Path, help="config file (default: <root>/verbump.toml)")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("status", help="show every package")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    for name, func, help_ in (("plan", cmd_plan, "show what would release"),
                              ("apply", cmd_apply, "write the versions and changelogs")):
        s = sub.add_parser(name, help=help_)
        src = s.add_mutually_exclusive_group()
        src.add_argument("--bump", choices=semver.BUMPS, type=str.lower, help="bump every changed package by this")
        src.add_argument("--branch", help="pick the bump from a branch name, like trunk-semver")
        s.add_argument("--previous", help="trunk-semver previous-version; with --version-from, gives the bump")
        s.add_argument("--version-from", dest="new_version", metavar="VERSION",
                       help="trunk-semver version output (the new version)")
        s.add_argument("--exact", action="append", default=[], metavar="NAME=X.Y.Z",
                       help="release a package at exactly this version, changed or not")
        s.add_argument("--release-branch", metavar="BRANCH",
                       help="release/<package>/X.Y.Z (or release/X.Y.Z with one package) sets --exact")
        s.add_argument("--only", action="append", default=[], metavar="NAME", help="limit to these packages")
        s.add_argument("--json", action="store_true", help="print the plan as JSON")
        s.add_argument("--plan-out", type=Path, help="also write the plan as JSON to this file")
        if name == "apply":
            s.add_argument("--date", help="release date (default: today, UTC)")
        s.set_defaults(func=func)

    s = sub.add_parser("tag", help="create the git tags of a plan")
    s.add_argument("--plan", type=Path, required=True)
    s.set_defaults(func=cmd_tag)

    s = sub.add_parser("notes", help="print a version's changelog section")
    s.add_argument("package")
    s.add_argument("version", nargs="?")
    s.set_defaults(func=cmd_notes)

    s = sub.add_parser("set", help="write an exact version into one package's files and changelog")
    s.add_argument("package")
    s.add_argument("version")
    s.add_argument("--date")
    s.set_defaults(func=cmd_set)

    s = sub.add_parser("check", help="exit 1 if a package's version files disagree")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("init", help="write a starter verbump.toml")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("demo", help="a narrated release in a throwaway repo")
    s.add_argument("--dir", type=Path, help="build the demo repo here and keep it (an empty or new folder)")
    s.add_argument("--setup-only", action="store_true", help="only build the demo repo and print its path")
    s.set_defaults(func=cmd_demo)
    return p


def config(args) -> Config:
    return load(args.config or args.root / "verbump.toml")


def resolve_bump(args) -> str:
    if args.bump:
        return args.bump
    if args.previous or args.new_version:
        if not (args.previous and args.new_version):
            raise ValueError("--previous and --version-from go together")
        return semver.bump_between(args.previous, args.new_version)
    if args.branch:
        return semver.bump_for_branch(args.branch)
    return "patch"


def build_plan(args):
    cfg = config(args)
    bump = resolve_bump(args)
    exact = release.exact_from_branch(cfg, args.release_branch)
    for item in args.exact:
        name, sep, version = item.partition("=")
        if not sep:
            raise ValueError(f"--exact {item!r}: use NAME=X.Y.Z")
        exact[name] = version
    releases = release.plan(args.root, cfg, bump, exact, args.only)
    return cfg, bump, releases


def report(args, cfg, bump, releases) -> None:
    data = release.to_json(cfg, bump, releases)
    if args.plan_out:
        args.plan_out.write_text(json.dumps(data, indent=2) + "\n")
    if args.json:
        print(json.dumps(data, indent=2))
    elif not releases:
        print("nothing to release")
    else:
        for r in releases:
            print(f"{r.name}: {r.previous or '-'} -> {r.version} ({r.reason}, tag {r.tag})")


def cmd_plan(args) -> int:
    report(args, *build_plan(args))
    return 0


def cmd_apply(args) -> int:
    cfg, bump, releases = build_plan(args)
    touched = release.apply(args.root, cfg, releases, args.date)
    report(args, cfg, bump, releases)
    for path in touched:
        print(f"  wrote {path}", file=sys.stderr)
    return 0


def cmd_tag(args) -> int:
    data = json.loads(args.plan.read_text())
    for r in data["releases"]:
        gitutil.git(args.root, "tag", "-a", r["tag"], "-m", f"{r['name']} {r['version']}")
        print(r["tag"])
        if r.get("major_tag"):
            gitutil.git(args.root, "tag", "-f", r["major_tag"])
            print(r["major_tag"])
    return 0


def cmd_notes(args) -> int:
    cfg = config(args)
    pkg = cfg.get(args.package)
    version = semver.normalize(args.version) if args.version else release.file_version(args.root, pkg)
    if not version:
        raise ValueError(f"{pkg.name} has no version files; pass the version")
    path = args.root / pkg.changelog_path if pkg.changelog_path else None
    print(changelog.notes(path.read_text() if path and path.is_file() else "", version))
    return 0


def cmd_set(args) -> int:
    cfg = config(args)
    pkg = cfg.get(args.package)
    version = semver.normalize(args.version)
    r = release.Release(name=pkg.name, path=pkg.path, previous=None, version=version, tag=pkg.tag(version),
                        major_tag=None, changelog=pkg.changelog_path, reason="set")
    release.apply(args.root, cfg, [r], args.date)
    print(f"set {pkg.name} {version}")
    return 0


def cmd_check(args) -> int:
    cfg = config(args)
    bad = 0
    for pkg in cfg.packages:
        try:
            v = release.file_version(args.root, pkg)
            print(f"{pkg.name}: {v or 'no version files'}")
        except (release.ReleaseError, ValueError) as e:
            print(f"{pkg.name}: {e}", file=sys.stderr)
            bad += 1
    return 1 if bad else 0


def cmd_status(args) -> int:
    cfg = config(args)
    tags = gitutil.tags_merged(args.root)
    rows = []
    for pkg in cfg.packages:
        st = release.state(args.root, pkg, tags)
        rows.append({"name": pkg.name, "path": pkg.path, "version": st.file_version, "last_tag": st.last_tag,
                     "changed": len(st.changed)})
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        table = [(r["name"], r["path"], r["version"] or "-", r["last_tag"] or "(no tag)", f"{r['changed']} changed")
                 for r in rows]
        widths = [max(len(row[i]) for row in table) for i in range(4)]
        for row in table:
            print("  ".join(cell.ljust(w) for cell, w in zip(row[:4], widths, strict=True)) + "  " + row[4])
    return 0


def cmd_init(args) -> int:
    path = args.config or args.root / "verbump.toml"
    if path.exists():
        raise ValueError(f"{path} already exists")
    path.write_text(STARTER)
    print(f"wrote {path}")
    return 0


def cmd_demo(args) -> int:
    from verbump import demo

    return demo.main(keep=args.dir, setup_only=args.setup_only)
