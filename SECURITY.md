# Security

verbump rewrites files in your repo and, in CI, its output is committed, tagged and pushed with write access.

- **It only rewrites what you list.** verbump writes the version files in `verbump.toml` and each package's changelog, nothing else, and only at the matched version. Review the release commit like any other change.
- **Changelogs and commit subjects become release notes.** When a package has no `Unreleased` notes, verbump lists the commit subjects that touched it. Don't put secrets in commit messages or changelogs.
- **Patterns are your regexes.** A `pattern` in `verbump.toml` runs against your own files; keep config changes reviewed like code (this repo's `CODEOWNERS` covers `verbump.toml`).

## Reporting a vulnerability

Report it privately at **[Security → Report a vulnerability](https://github.com/TheKathan/verbump/security/advisories/new)** (GitHub private vulnerability reporting). Please don't open a public issue. Include the verbump version (`verbump --version`), what you did, and what happened. You should get a reply within 7 days.

## How the repository is protected
- `main` accepts changes only through pull requests with all checks passing. Nobody can force-push to it or delete it.
- The code owner (`.github/CODEOWNERS`) reviews and merges every pull request. As the sole maintainer, the code owner can also merge their own pull requests without a second reviewer.
- Release tags (`v*`) can be created or moved only by the release workflow's deploy key. That key is stored in a `release` environment that only `main` can use, and only the job that pushes loads it; the tests run in a separate job without it.
- Each exact version tag (`vX.Y.Z`) is created once and never moved; only the major tag (`v1`) moves to the latest release.
- The PyPI package (`verbump-cli`) is published from the release workflow through Trusted Publishing (OIDC), in a `pypi` environment limited to `main`. Only that job can request an OIDC token; no PyPI token is stored. See [docs/publishing.md](docs/publishing.md).
- Workflows run with read-only tokens by default, use only GitHub-owned or `TheKathan/*` actions (plus the PyPI publisher) pinned to commit SHAs, and Dependabot keeps those pins current.
