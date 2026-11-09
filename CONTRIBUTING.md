# Contributing

Everyone taking part in verbump follows the [code of conduct](CODE_OF_CONDUCT.md). Bugs and ideas go in an issue, using one of the [templates](https://github.com/TheKathan/verbump/issues/new/choose).

## Ground rules
- **Standard library only.** verbump must run anywhere Python 3.11+ runs, with nothing else installed. CI installs only the package itself.
- **Stack-agnostic.** verbump reads and writes version files; it never runs a stack's own tooling (`npm`, `cargo`, `dotnet` …). A new file type is a `Kind` in `src/verbump/files.py`, with a realistic sample in `tests/test_files.py`.
- **`verbump.toml` is a public contract.** Keys are only added within 1.x, never renamed or removed, and unknown keys stay an error so typos don't pass silently.
- **The CLI and the plan JSON are public contracts too.** The action ([verbump-action](https://github.com/TheKathan/verbump-action)) and people's workflows call commands, flags and plan fields by name. Only add within 1.x; to rename something, keep the old spelling working for at least one minor version.
- **Never move an exact tag.** Anything that writes tags creates `<tag>` once; only major tags (`vX`) move.

## Development
```bash
make test      # unit tests, plus end-to-end tests against throwaway git repos
make lint      # ruff, via uvx
PYTHONPATH=src python3 -m verbump demo    # run the CLI from the checkout
```

Every change needs a test in `tests/`. The end-to-end tests build real git repos with `tests/helpers.py`.

## Layout
| Path | What it holds |
|---|---|
| `src/verbump/cli.py` | commands and argument parsing |
| `src/verbump/config.py` | `verbump.toml` loading and checks, packages, tag formats |
| `src/verbump/files.py` | version file kinds: patterns, `after`, `replace_all` |
| `src/verbump/release.py` | what changed, what releases at which version, writing it |
| `src/verbump/changelog.py` | Keep a Changelog sections and release notes |
| `src/verbump/semver.py` | parse, compare and bump `X.Y.Z` |
| `src/verbump/gitutil.py` | the git commands verbump runs |
| `src/verbump/demo.py` | `verbump demo` and its throwaway repo |
| `assets/demo.tape` | the README recording: `vhs assets/demo.tape` |

## Branches and releases
- Never push to `main`. Open a pull request from a branch whose name picks the version bump ([trunk-semver](https://github.com/TheKathan/trunk-semver)):
  - `feature/<topic>` or `feat/<topic>` bumps the minor version (`v1.2.0` → `v1.3.0`);
  - any other branch name (`fix/`, `docs/`, `chore/`, `refactor/`, `ci/` …) bumps the patch version;
  - `release/X.Y.Z` releases exactly `vX.Y.Z`. Use it only for a new major version, and bump `major-version` in `release.yml` in the same PR.
- Merging the PR releases it. `.github/workflows/release.yml` runs the tests (without the deploy key), then verbump releases itself from its own source: it writes `src/verbump/__init__.py` and `CHANGELOG.md`, creates the `vX.Y.Z` tag once (only the major tag `v1` moves), and publishes a GitHub release.
- The release also publishes `verbump-cli` to PyPI (Trusted Publishing) while the repository variable `PUBLISH_PYPI` is `true`. The one-time setup is in [docs/publishing.md](docs/publishing.md).
- Don't edit version numbers by hand. `verbump check` verifies they agree, and the release runs it.

## What a pull request needs
Repository rulesets require all of these on `main`:
- an approving review from the code owner (`@TheKathan`, see `.github/CODEOWNERS`), given after your last push; new pushes dismiss earlier approvals;
- all review threads resolved;
- every `test` job and `build` green and up to date with `main`;
- a merge commit or a squash merge (no rebase merges; history on `main` is never rewritten).

As the sole maintainer, the code owner can merge their own pull requests without a second review; they still need green checks.

Pull requests from forks run CI only after a maintainer approves the run.

## Commits and pull requests
- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat(files): …`, `fix(changelog): …`, `docs: …`.
- **Never add `Co-Authored-By` lines** (for people or AI tools) to commit messages.
- Update `CHANGELOG.md` under the `Unreleased` heading, and the README when behaviour changes. Without notes, the release lists the commit subjects instead.
