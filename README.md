# verbump

Version and changelog bumps for repos.

A repo holds one package or several, each with its own version. You tell verbump *how much* to bump, with a flag, a branch name, or the outputs of a tool such as [trunk-semver](https://github.com/TheKathan/trunk-semver). verbump works out *what* to bump: the packages whose folders changed since each package's own last tag. For each one it writes the new version into its files, turns its changelog's "Unreleased" notes into a release section, and plans a `<package>/vX.Y.Z` tag and a GitHub release. Packages that didn't change stay where they are.

Python 3.11+, standard library only.

## How it works

```
merge PR feat/orders  ─►  trunk-semver: v0.4.0 → v0.5.0  ─►  bump = minor
                                                               │
           verbump: which packages changed since their last tag?
             services/api   (api/v1.4.0..HEAD touches it)   → 1.5.0
             apps/web       (no changes)                    → stays 0.3.0
             libs/shared    (watched by api)                → counted for api
                                                               │
   writes pyproject.toml, __init__.py, services/api/CHANGELOG.md
   commit "chore(release): api 1.5.0" → tag api/v1.5.0 → GitHub release "api 1.5.0"
```

- **Version source.** Each package's version files are the source of truth. If the files and the last tag disagree, verbump bumps from the higher of the two.
- **First release.** A package with no tag yet is released at the version its files already have. A package with no version files starts from `initial_version` (`0.0.0`) and is bumped.
- **Changelog.** The notes under `## [Unreleased]` become `## [X.Y.Z] - <date>`. If nobody wrote notes, the section lists the subjects of the commits that touched the package since its last tag, leaving out `chore(release)` and merge commits. A missing `CHANGELOG.md` is created.
- **Exact versions.** A PR from `release/<package>/X.Y.Z` releases that package at exactly X.Y.Z. In a single-package repo, `release/X.Y.Z` is enough. Use this for a new major, which bumps can't reach.
- **Safe to re-run.** Tags point at the release commit, so a second run finds nothing new to release. An existing tag is never moved; only the optional major tag (`vX`) is.

## Configure

`verbump.toml` at the repo root:

```toml
tag_format = "{name}/v{version}"   # default for every package
changelog = "CHANGELOG.md"          # relative to the package path; "" for none

[packages.api]
path = "services/api"
files = ["pyproject.toml", "src/api/__init__.py"]
watch = ["libs/shared"]             # other repo paths whose changes release this package
exclude = ["*.md", "docs/*"]        # changes only here don't release it

[packages.web]
path = "apps/web"
files = ["package.json"]
```

Files are relative to the package `path`. These files are recognised by name:

| File | Matches |
|---|---|
| `pyproject.toml`, `Cargo.toml` | `version = "X.Y.Z"` |
| `package.json` | `"version": "X.Y.Z"` |
| `Chart.yaml` | `version: X.Y.Z` |
| `VERSION` | the whole file |
| `*.py` | `__version__ = "X.Y.Z"` |
| `*.csproj`, `*.props` | `<Version>X.Y.Z</Version>` |

Any other file takes a regex with a `version` group, for example `{ path = "deploy/values.yaml", pattern = 'imageTag:\s*"(?P<version>\d+\.\d+\.\d+)"' }`. Only the first match is rewritten.

Other keys, per package or at the top level: `major_tag = true` also moves a `<name>/vX` tag, which is useful for GitHub Actions published from a monorepo. `commit_message` (top level) defaults to `"chore(release): {releases}"`.

For a single-package repo, use `tag_format = "v{version}"` and one package at `path = "."`. This repo's own [`verbump.toml`](verbump.toml) is an example of that, and [`examples/monorepo/verbump.toml`](examples/monorepo/verbump.toml) is a monorepo example.

## Commands

```
verbump status                                     packages, file versions, last tags, pending changes
verbump plan  --previous v1.0.0 --version-from v1.1.0   what would release (trunk-semver's outputs)
verbump apply --bump minor --plan-out plan.json    write versions and changelogs, save the plan
verbump tag   --plan plan.json                     create the planned tags (and major tags)
verbump notes <package> [<version>]                a version's changelog section, for a release body
verbump set   <package> <version>                  write an exact version into one package
verbump check                                      exit 1 if a package's version files disagree
verbump init                                       write a starter verbump.toml
```

`plan` and `apply` get the bump from one of these sources:
- `--bump major|minor|patch`;
- `--previous` and `--version-from`, trunk-semver's `previous-version` and `version` outputs, from which verbump works out the bump;
- `--branch <name>`, which applies trunk-semver's branch rule without trunk-semver;
- nothing, which means a patch.

Further options:
- `--release-branch <branch>` and `--exact NAME=X.Y.Z` force an exact version.
- `--only NAME` limits the run to some packages.
- `--json` prints the plan.

Global options: `-C <repo root>` and `-c <config file>`.

The plan JSON has the shape `{"bump", "commit_message", "releases": [{"name", "path", "previous", "version", "tag", "major_tag", "changelog", "reason", "changed"}]}`.

## Use it in a workflow

[`.github/workflows/release.yml`](.github/workflows/release.yml) is the whole pipeline, and this repo releases itself with it. It runs in this order:
1. Run the tests, skipping the bot's own `chore(release)` commit.
2. Find the merged PR's source branch.
3. Run trunk-semver against a local mirror, so its repo-wide `vX.Y.Z` tag never reaches GitHub. Only the bump it computes is used.
4. Run `verbump apply` with trunk-semver's `previous-version` and `version` and the source branch, then `verbump check`.
5. Commit, then `verbump tag`, and push the commit and tags. The job refuses to overwrite an existing tag on GitHub.
6. Run `gh release create` for each package, with `verbump notes` as the body.

To use it in another repo, copy the workflow and add a `verbump.toml`. Then replace the `env` block, which runs verbump from this repo's source, with an install step. This repo is private, so the install needs a token with read access to it:

```yaml
env:
  VERBUMP: verbump

# in the release job, after setup-python:
      - name: Install verbump
        run: python3 -m pip install "git+https://x-access-token:${{ secrets.VERBUMP_READ_TOKEN }}@github.com/TheKathan/verbump@v0"
```

`@v0` follows the latest 0.x release. To pin one, use `@v0.1.0`.

If `main` has a ruleset that requires PRs, add a write deploy key as the `RELEASE_DEPLOY_KEY` secret and let only that key bypass the ruleset, as baton does. Without the secret, the job's token pushes.

## Develop

```
make test    # unit tests and end-to-end tests against throwaway git repos
make lint    # ruff
```

The branch name picks the release: `feature/…` gives a minor version, anything else a patch, and `release/X.Y.Z` an exact version. Add notes under `## [Unreleased]` in `CHANGELOG.md`.
