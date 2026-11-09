# verbump

Version and changelog bumps for repos.

A repo holds one package or several, each with its own version. You tell verbump *how much* to bump, with a flag, a branch name, or the outputs of a tool such as [trunk-semver](https://github.com/TheKathan/trunk-semver). verbump works out *what* to bump: the packages whose folders changed since each package's own last tag. For each one it writes the new version into its files, turns its changelog's "Unreleased" notes into a release section, and plans a `<package>/vX.Y.Z` tag and a GitHub release. Packages that didn't change stay where they are.

It works with any stack: it reads and writes the version in Node, Python, Rust, Go, .NET, Java, Ruby, PHP, Elixir, Dart, Helm and Docker files, or in any file you give a pattern. It needs Python 3.11+ and nothing else. In GitHub Actions, [verbump-action](https://github.com/TheKathan/verbump-action) runs it for a repo on any stack.

## Install

```
pipx install verbump-cli        # or: uv tool install verbump-cli, pip install verbump-cli
verbump --version
```

The package is `verbump-cli` on PyPI because the name `verbump` belongs to an unrelated project. The command it installs is `verbump`.

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

Files are relative to the package `path`. verbump picks the kind of file from its name:

| Stack | Files | Matches |
|---|---|---|
| Node, PHP, Deno | `package.json`, `composer.json`, `deno.json`, `jsr.json`, `manifest.json` | `"version": "X.Y.Z"` |
| Python | `pyproject.toml`, `setup.cfg`, `*.py` | `version = "X.Y.Z"`, `version = X.Y.Z`, `__version__ = "X.Y.Z"` |
| Rust | `Cargo.toml` | `version = "X.Y.Z"` at the start of a line |
| .NET | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.props` | `<Version>` or `<VersionPrefix>` |
| .NET | `AssemblyInfo.cs` | every `Assembly[File\|Informational]Version("X.Y.Z…")` |
| Java, Kotlin | `pom.xml` | the project's `<version>`, after `</parent>` when there is one |
| Java, Kotlin | `build.gradle`, `build.gradle.kts`, `gradle.properties` | `version = "X.Y.Z"`, `version 'X.Y.Z'`, `version=X.Y.Z` |
| Ruby | `version.rb`, `*.gemspec` | `VERSION = "X.Y.Z"`, `.version = "X.Y.Z"` |
| Elixir | `mix.exs` | `version: "X.Y.Z"` |
| Dart, Flutter | `pubspec.yaml` | `version: X.Y.Z` (a `+build` suffix is kept) |
| Helm | `Chart.yaml` | `version: X.Y.Z` (kind `helm` also moves `appVersion`) |
| Docker | `Dockerfile` | `LABEL … version="X.Y.Z"` |
| Any | `VERSION`, `VERSION.txt`, `version.txt`, `.version` | the whole file |
| Go, Swift, … | no file | the version lives only in the tags; use `tag_format = "{path}/v{version}"` for Go modules |

A file can also be a table:

```toml
files = [
  { path = "chart/Chart.yaml", kind = "helm" },                  # a kind for any file name
  { path = "deploy/values.yaml",                                  # or your own pattern
    pattern = 'tag:\s*"(?P<version>\d+\.\d+\.\d+)"',
    after = "image:",                                             # search only after this text
    replace_all = true },                                         # rewrite every match, not just the first
]
```

The kinds are `json`, `toml`, `yaml`, `helm`, `plain`, `python`, `msbuild`, `assemblyinfo`, `maven`, `properties`, `gradle`, `ruby`, `elixir` and `dockerfile`. A `pattern` needs a `version` group. Unless `replace_all` is set, only the first match is rewritten. When there are several matches, the first is read.

`tag_format` can use `{name}`, `{path}` and `{version}`.

Other keys, per package or at the top level: `major_tag = true` also moves a `<name>/vX` tag, which is useful for GitHub Actions published from a monorepo. `commit_message` (top level) defaults to `"chore(release): {releases}"`.

For a single-package repo, use `tag_format = "v{version}"` and one package at `path = "."`. This repo's own [`verbump.toml`](verbump.toml) is an example of that, and [`examples/monorepo/verbump.toml`](examples/monorepo/verbump.toml) is a monorepo with Python, Node, .NET, Maven, Go and Helm packages.

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

In GitHub Actions, use [TheKathan/verbump-action](https://github.com/TheKathan/verbump-action). It installs `verbump-cli` from PyPI, then:
1. applies the bump;
2. commits, tags and pushes;
3. publishes a GitHub release per package.

It takes the bump as an input, from any source (trunk-semver, a branch name or a fixed value), and doesn't run trunk-semver itself.

Anywhere else, the CLI does the same work:

```
verbump apply --branch "$PR_BRANCH" --release-branch "$PR_BRANCH" --plan-out plan.json
verbump check
git commit -am "$(jq -r .commit_message plan.json)"
verbump tag --plan plan.json
git push origin HEAD:main --follow-tags
```

This repo releases itself with [`.github/workflows/release.yml`](.github/workflows/release.yml), running verbump from its own source. It runs in this order:
1. Run trunk-semver against a local mirror, so its repo-wide tag never reaches GitHub, and take the bump from its `previous-version` and `version`.
2. Run `verbump apply`.
3. Commit, tag and push.
4. Publish the GitHub release.
5. Build the sdist and the wheel.
6. Upload them to PyPI, when the `PUBLISH_PYPI` variable is `true`.

## Develop

```
make test    # unit tests and end-to-end tests against throwaway git repos
make lint    # ruff
```

The branch name picks the release: `feature/…` gives a minor version, anything else a patch, and `release/X.Y.Z` an exact version. Add notes under `## [Unreleased]` in `CHANGELOG.md`.
