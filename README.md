<h1 align="center">verbump</h1>

<p align="center">
  <a href="https://github.com/TheKathan/verbump/actions/workflows/test.yml"><img alt="tests" src="https://github.com/TheKathan/verbump/actions/workflows/test.yml/badge.svg"></a>
  <a href="https://pypi.org/project/verbump-cli/"><img alt="PyPI" src="https://img.shields.io/pypi/v/verbump-cli"></a>
  <img alt="license" src="https://img.shields.io/github/license/TheKathan/verbump">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-%E2%89%A5%203.11-3776AB">
  <img alt="dependencies: none" src="https://img.shields.io/badge/dependencies-none-brightgreen">
</p>

**Version and changelog bumps for repos: only the packages that changed move.**

verbump finds the packages in your repo that changed since their own last tag, writes each one's new version into its files, and turns its changelog's `## [Unreleased]` notes into the release. One package or fifty, Python, Node, .NET, Java, Rust, Go or anything with a version in a file. One CLI, one `verbump.toml`, no dependencies.

**Try it in one command:** `uvx --from verbump-cli verbump demo`

<p align="center"><img alt="verbump in a repo with two packages. verbump status shows api at 1.4.0 with 0 changed files and web at 0.3.0 with 2 changed files. git log shows a commit, feat(web): checkout page, that touched apps/web. verbump apply --branch feat/checkout bumps web from 0.3.0 to 0.4.0, tag web/v0.4.0, and writes apps/web/package.json and apps/web/CHANGELOG.md. git diff shows the version going from 0.3.0 to 0.4.0, and verbump notes web prints the release notes: Added, Checkout page." src="https://raw.githubusercontent.com/TheKathan/verbump/main/assets/demo.gif" width="800"><br><sub>A PR from <code>feat/checkout</code> changed only <code>apps/web</code>: web gets a minor bump and its release notes, api stays at 1.4.0.</sub></p>

## Try it in 60 seconds

With verbump [installed](#quick-start), this builds the repo from the recording in a scratch folder and releases it:

```bash
verbump demo --dir verbump-try --setup-only && cd verbump-try
verbump status                          # api and web, both tagged; web has changes
verbump plan --branch feat/checkout     # web: 0.3.0 -> 0.4.0 (minor, tag web/v0.4.0)
verbump apply --branch feat/checkout    # writes apps/web/package.json and CHANGELOG.md
verbump notes web                       # the notes for the GitHub release
```

Or run `verbump demo` for a narrated replay in a temporary folder.

## Why verbump

- **Only what changed moves.** Each package is released from its own last tag, so a fix in one service doesn't bump the other nine.
- **Release notes you already wrote.** The `Unreleased` notes become the version's section and the GitHub release body; with no notes, the commit subjects that touched the package.
- **Any stack.** It reads and writes versions in `package.json`, `pyproject.toml`, `Cargo.toml`, `.csproj`, `pom.xml`, Gradle, Helm charts, Dockerfiles and more, or any file you give a pattern. Go-style tags work too.
- **You choose the bump.** A flag, the PR's branch name, or [trunk-semver](https://github.com/TheKathan/trunk-semver)'s outputs. A `release/<package>/X.Y.Z` branch cuts an exact version.
- **Safe to re-run.** Tags are created once and never moved; a second run finds nothing to release.
- **Nothing to run.** Python 3.11+ and the standard library; no server, no plugins per language.

## What it's for

| Use | What you get |
|---|---|
| **A repo with several services or libraries** | Per-package versions, tags (`api/v1.5.0`) and changelogs, from one config. [Example](https://github.com/TheKathan/verbump/blob/main/examples/monorepo/verbump.toml) |
| **A single package** | `tag_format = "v{version}"` and one package at `.`; verbump releases itself this way. [Its config](https://github.com/TheKathan/verbump/blob/main/verbump.toml) |
| **GitHub Actions** | [verbump-release](https://github.com/TheKathan/verbump-release) releases on merge: bumps, commits, tags, pushes and publishes a GitHub release per package. [verbump-check](https://github.com/TheKathan/verbump-check) previews a PR's release and fails early. [setup-verbump](https://github.com/TheKathan/setup-verbump) just installs the CLI. |
| **Any other CI** | Four commands: `apply`, `check`, `tag`, `notes`. [Recipe](#using-it-in-ci) |

## Quick start

Install it. The PyPI package is `verbump-cli`, because the name `verbump` belongs to an unrelated project. The command it installs is `verbump`.

```bash
pipx install verbump-cli        # or: uv tool install verbump-cli, pip install verbump-cli
verbump --version
```

Declare your packages in `verbump.toml` at the repo root. `verbump init` writes a starter file. A minimal one looks like this:

```toml
tag_format = "{name}/v{version}"

[packages.api]
path = "services/api"
files = ["pyproject.toml", "src/api/__init__.py"]

[packages.web]
path = "apps/web"
files = ["package.json"]
```

See what would release. Here a commit changed `services/api` since its last tag `api/v1.4.0`, and nothing changed in `apps/web`:

```console
$ verbump plan --bump minor
api: 1.4.0 -> 1.5.0 (minor, tag api/v1.5.0)
```

Write the new versions and changelogs. `apply` changes files only. It does not commit or tag.

```console
$ verbump apply --bump minor --plan-out plan.json
api: 1.4.0 -> 1.5.0 (minor, tag api/v1.5.0)
  wrote services/api/pyproject.toml
  wrote services/api/src/api/__init__.py
  wrote services/api/CHANGELOG.md
```

The `wrote` lines go to stderr. Commit the changes, then `verbump tag --plan plan.json` creates the tags. For a full CI recipe, see [Using it in CI](#using-it-in-ci).

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

The bump can come from trunk-semver, as drawn, or from `--bump` or a branch name. The commit, tag and release steps are your CI's job; verbump plans them and writes the files.

- **What counts as a change.** A package changed if any file under its `path` or its `watch` paths changed since the package's last tag, other than files that match `exclude`. A package with no tag yet counts every tracked file under those paths.
- **Version source.** Each package's version files are the source of truth. If the files and the last tag disagree, verbump bumps from the higher of the two. If a package's version files disagree with each other, verbump stops with an error.
- **First release.** A package with no tag yet is released at the version its files already have. A package with no version files starts from `initial_version` (`0.0.0`) and is bumped.
- **Changelog.** The notes under `## [Unreleased]` become `## [X.Y.Z] - <date>`. If nobody wrote notes, the section lists the subjects of the commits that touched the package since its last tag, leaving out `chore(release)` and merge commits. A missing `CHANGELOG.md` is created. A section for that version that already exists is left alone.
- **Exact versions.** A PR from `release/<package>/X.Y.Z` releases that package at exactly X.Y.Z, changed or not. In a single-package repo, `release/X.Y.Z` is enough. Use this for a new major, which bumps can't reach. An exact version must be newer than the package's last release.
- **Safe to re-run.** Tags point at the release commit, so a second run finds nothing new to release. If the planned tag already exists, verbump stops instead of moving it. Only the optional major tag (`vX`) is moved.

## Configuration

`verbump.toml` at the repo root. Use `-c <file>` for another path.

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

Package names use letters, digits, `.`, `_` and `-`. verbump rejects unknown keys.

### Keys

`tag_format`, `changelog` and `major_tag` can be set at the top level as defaults for every package, and again per package.

| Key | Where | Default | Meaning |
|---|---|---|---|
| `tag_format` | top level, package | `{name}/v{version}` | Tag name. Uses `{name}`, `{path}` and `{version}`; `{version}` appears exactly once. `{path}` can't be used at the repo root. Two packages can't share a tag. |
| `changelog` | top level, package | `CHANGELOG.md` | Changelog file, relative to the package `path`. `""` turns it off. |
| `major_tag` | top level, package | `false` | Also move a major tag, such as `api/v1`, on each release. |
| `commit_message` | top level | `chore(release): {releases}` | Commit message in the plan. `{releases}` becomes `api 1.5.0, web 0.3.1`. |
| `path` | package | `.` | The package folder, relative to the repo root. It must stay inside the repo. |
| `files` | package | none | Files that carry the version, relative to `path`. See [Supported files](#supported-files). |
| `watch` | package | none | Other repo paths whose changes also release this package. |
| `exclude` | package | none | Glob patterns. Changes only to matching files don't release the package. Patterns match the repo path or the path relative to the package. |
| `initial_version` | package | `0.0.0` | Where a package with no tag and no version files starts. |

For a single-package repo, use `tag_format = "v{version}"` and one package at `path = "."`. This repo's own [`verbump.toml`](https://github.com/TheKathan/verbump/blob/main/verbump.toml) is an example. [`examples/monorepo/verbump.toml`](https://github.com/TheKathan/verbump/blob/main/examples/monorepo/verbump.toml) is a monorepo with Python, Node, .NET, Maven, Go and Helm packages.

### Files as tables

A file can be a table, to pick a kind for any file name or to give your own pattern:

```toml
files = [
  { path = "chart/Chart.yaml", kind = "helm" },                  # a kind for any file name
  { path = "deploy/values.yaml",                                  # or your own pattern
    pattern = 'tag:\s*"(?P<version>\d+\.\d+\.\d+)"',
    after = "image:",                                             # search only after this text
    replace_all = true },                                         # rewrite every match, not just the first
]
```

| Key | Meaning |
|---|---|
| `path` | The file, relative to the package `path`. Required. |
| `kind` | A built-in matcher: `json`, `toml`, `yaml`, `helm`, `plain`, `python`, `msbuild`, `assemblyinfo`, `maven`, `properties`, `gradle`, `ruby`, `elixir` or `dockerfile`. |
| `pattern` | Your own regex. It needs a `(?P<version>...)` group. It wins over `kind`. |
| `after` | Search only after the first occurrence of this text. |
| `replace_all` | Rewrite every match. By default only the first match is rewritten, and when there are several matches the first is read. |

## Supported files

verbump picks the kind of a file from its name, so most configs only list paths. Any other file needs a `kind` or a `pattern`.

| Stack | Files | Matches |
|---|---|---|
| Node, PHP, Deno | `package.json`, `composer.json`, `deno.json`, `jsr.json`, `manifest.json` | `"version": "X.Y.Z"` |
| Python | `pyproject.toml` | `version = "X.Y.Z"` at the start of a line |
| Python | `setup.cfg` | `version = X.Y.Z` |
| Python | `*.py` | `__version__ = "X.Y.Z"` |
| Rust | `Cargo.toml` | `version = "X.Y.Z"` at the start of a line |
| .NET | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.props` | `<Version>` or `<VersionPrefix>` |
| .NET | `AssemblyInfo.cs` | every `Assembly[File\|Informational]Version("X.Y.Z...")` |
| Java, Kotlin | `pom.xml` | the project's `<version>`, after `</parent>` when there is one |
| Java, Kotlin | `build.gradle`, `build.gradle.kts` | `version = "X.Y.Z"` or `version 'X.Y.Z'` |
| Java, Kotlin | `gradle.properties` | `version=X.Y.Z` |
| Ruby | `version.rb`, `*.gemspec` | `VERSION = "X.Y.Z"`, `.version = "X.Y.Z"` |
| Elixir | `mix.exs` | `version: "X.Y.Z"` |
| Dart, Flutter | `pubspec.yaml` | `version: X.Y.Z` (a `+build` suffix is kept) |
| Helm | `Chart.yaml` | `version: X.Y.Z`. Set `kind = "helm"` to move `appVersion` too. |
| Docker | `Dockerfile` | `LABEL ... version="X.Y.Z"` |
| Any | `VERSION`, `VERSION.txt`, `version.txt`, `.version` | the whole file |
| Go, Swift, ... | no file | the version lives only in the tags; use `tag_format = "{path}/v{version}"` for Go modules |

A `v` prefix is read in `Chart.yaml` with `kind = "helm"` and in plain version files. Versions are always `X.Y.Z`.

## Commands

```
verbump [-C ROOT] [-c CONFIG] <command>
```

| Command | What it does |
|---|---|
| `status [--json]` | Lists each package with its file version, last tag and number of changed files. |
| `plan [options]` | Shows what would release. Changes nothing. |
| `apply [options] [--date YYYY-MM-DD]` | Writes versions and changelogs, and prints the plan. Doesn't commit or tag. `--date` defaults to today, UTC. |
| `tag --plan FILE` | Creates the annotated tags in a saved plan, and moves its major tags. Doesn't push. |
| `notes <package> [<version>]` | Prints a version's changelog section, for a release body. Without a version, it uses the package's file version. |
| `set <package> <version> [--date D]` | Writes an exact version into one package's files and changelog. |
| `check` | Prints each package's file version. Exits 1 if a package's version files disagree. |
| `init` | Writes a starter `verbump.toml`. It won't overwrite an existing one. |
| `demo [--dir D] [--setup-only]` | A narrated release in a throwaway repo with a Python and a Node package. `--dir` keeps the repo; `--setup-only` only builds it and prints its path. |

Global options: `-C <repo root>` (default `.`) and `-c <config file>` (default `<root>/verbump.toml`).

### Choosing the bump

`plan` and `apply` take the bump from one of these sources:

- `--bump major|minor|patch`.
- `--previous` and `--version-from`, which are trunk-semver's `previous-version` and `version` outputs. verbump works out the bump from the two. They go together.
- `--branch <name>`, which applies trunk-semver's branch rule without trunk-semver.
- Nothing, which means a patch.

`--bump` and `--branch` can't be combined. If you pass several sources, `--bump` wins, then `--previous` with `--version-from`, then `--branch`.

### Other options for `plan` and `apply`

| Option | Meaning |
|---|---|
| `--exact NAME=X.Y.Z` | Release a package at exactly this version, changed or not. Repeatable. |
| `--release-branch <branch>` | If the branch is `release/<package>/X.Y.Z` (or `release/X.Y.Z` with one package), it sets `--exact`. Other branches are ignored. |
| `--only NAME` | Limit the run to this package. Repeatable. |
| `--json` | Print the plan as JSON instead of text. |
| `--plan-out FILE` | Also write the plan as JSON to this file. |

### Output

`plan` and `apply` print one line per release, as `name: previous -> new (reason, tag T)`. The previous version is `-` for a package with no tag. With nothing to release they print `nothing to release`. The reason is the bump, `first release` or `exact`.

The plan JSON has the shape `{"bump", "commit_message", "releases": [{"name", "path", "previous", "version", "tag", "major_tag", "changelog", "reason", "changed"}]}`.

## Using it in CI

In GitHub Actions there are three actions, each in its own repo:

| Action | Use it to |
|---|---|
| [`TheKathan/verbump-release@v1`](https://github.com/TheKathan/verbump-release) | release on merge: apply the bump, commit, tag, push, and publish a GitHub release per package |
| [`TheKathan/verbump-check@v1`](https://github.com/TheKathan/verbump-check) | preview on a PR what merging it will release, with the release notes, and fail early if that release would fail |
| [`TheKathan/setup-verbump@v1`](https://github.com/TheKathan/setup-verbump) | put `verbump` on the PATH for your own steps, without touching the job's Python |

```yaml
# on push to main
- uses: actions/checkout@v7
  with:
    fetch-depth: 0
- uses: TheKathan/verbump-release@v1
```

The release action takes the bump as an input from any source: trunk-semver's outputs, the merged PR's branch name (the default), or a fixed value. It doesn't run trunk-semver itself.

Anywhere else, the CLI does the same work. This recipe takes the bump from the merged PR's branch name:

```bash
verbump apply --branch "$PR_BRANCH" --release-branch "$PR_BRANCH" --plan-out plan.json
verbump check
git commit -am "$(jq -r .commit_message plan.json)"
verbump tag --plan plan.json
git push origin HEAD:main --follow-tags
```

`--follow-tags` pushes the annotated tags. Major tags are lightweight and moved, so push them yourself, for example with `git push --force origin <major_tag>`. To create a GitHub release for each package, loop over the plan and use `verbump notes <name> <version>` as the release body.

This repo releases itself with [`.github/workflows/release.yml`](https://github.com/TheKathan/verbump/blob/main/.github/workflows/release.yml), running verbump from its own source. It runs in this order:

1. Run trunk-semver against a local mirror, so its repo-wide tag never reaches GitHub, and take the bump from its `previous-version` and `version`. When it gives no previous version, use the PR's branch name.
2. Run `verbump apply` and `verbump check`.
3. Commit, tag and push.
4. Publish the GitHub release.
5. Build the sdist and the wheel.
6. Upload them to PyPI, when the `PUBLISH_PYPI` variable is `true`.

## Contribute

Bugs, questions and ideas go to [issues](https://github.com/TheKathan/verbump/issues), and pull requests are welcome: see [CONTRIBUTING](https://github.com/TheKathan/verbump/blob/main/CONTRIBUTING.md) and the [code of conduct](https://github.com/TheKathan/verbump/blob/main/CODE_OF_CONDUCT.md). Issues about one of the GitHub Actions go to its repo: [verbump-release](https://github.com/TheKathan/verbump-release/issues), [verbump-check](https://github.com/TheKathan/verbump-check/issues) or [setup-verbump](https://github.com/TheKathan/setup-verbump/issues). If verbump saves you a release chore, a star helps others find it.

[CHANGELOG](https://github.com/TheKathan/verbump/blob/main/CHANGELOG.md) · [SECURITY](https://github.com/TheKathan/verbump/blob/main/SECURITY.md) · [Publishing](https://github.com/TheKathan/verbump/blob/main/docs/publishing.md) · [LICENSE](https://github.com/TheKathan/verbump/blob/main/LICENSE) (MIT)
