# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- The GitHub Actions are three Marketplace actions, each in its own repo: [verbump-release](https://github.com/TheKathan/verbump-release) (release on merge), [verbump-check](https://github.com/TheKathan/verbump-check) (preview a PR's release and fail early) and [setup-verbump](https://github.com/TheKathan/setup-verbump) (install the CLI). They replace TheKathan/verbump-action, which is gone. The README, CONTRIBUTING, the issue templates and the package links point at them.

## [1.0.1] - 2026-11-09

### Fixed
- The README recording renders on GitHub and PyPI: its alt text no longer contains `->`, which closed the image tag early.
- GitHub no longer counts `assets/demo.tape` as a language.

## [1.0.0] - 2026-11-09

The first stable release. `verbump.toml`, the commands and flags, and the plan JSON are public contracts from here on: within 1.x they only gain keys, flags and fields.

### Added
- `verbump demo`: a narrated release in a throwaway repo with a Python and a Node package. `--dir` keeps the repo, and `--setup-only` only builds it, to try the commands by hand.
- The README opens with a one-command try-out (`uvx --from verbump-cli verbump demo`), a recording of a release, and what verbump is for. The recording is rebuilt with `vhs assets/demo.tape`.
- CONTRIBUTING, SECURITY, a code of conduct, issue templates for bugs and feature requests, and [docs/publishing.md](docs/publishing.md) for the PyPI setup.

### Changed
- `verbump status` sizes its columns to their contents.
- The release workflow runs trunk-semver with `major-version: "1"`.

## [0.2.0] - 2026-11-09

### Added
- Version files for more stacks, picked by file name: `composer.json`, `deno.json`, `jsr.json`, `manifest.json`, `setup.cfg`, `*.fsproj`, `*.vbproj`, `<VersionPrefix>`, `AssemblyInfo.cs`, `pom.xml` (the project version, not the parent's), `build.gradle`, `build.gradle.kts`, `gradle.properties`, `version.rb`, `*.gemspec`, `mix.exs`, `pubspec.yaml` and `Dockerfile` labels.
- A file entry can name a `kind` (`json`, `toml`, `yaml`, `helm`, `plain`, `python`, `msbuild`, `assemblyinfo`, `maven`, `properties`, `gradle`, `ruby`, `elixir`, `dockerfile`) for any file name. It can also search only `after` a marker, and rewrite every match with `replace_all`. Kind `helm` moves `version` and `appVersion` together.
- `tag_format` can use `{path}`, for Go-style module tags such as `services/billing/v1.2.3`.
- Published on PyPI as `verbump-cli` (the command is `verbump`): `pipx install verbump-cli`. The release workflow builds the sdist and the wheel for every release and uploads them when the `PUBLISH_PYPI` variable is `true`. PRs build the package, install the wheel and run it.
- The README is rewritten: a quick start, a configuration reference, the supported files by stack, a command reference and CI recipes.
- The MIT license.
- The GitHub Action lives in its own repo, [TheKathan/verbump-action](https://github.com/TheKathan/verbump-action).

## [0.1.1] - 2026-11-09

### Changed
- The release workflow runs trunk-semver with `major-version: "0"`, so its versions follow this repo's own v0 tags. When trunk-semver gives no previous version, the bump comes from the PR's branch name.
- The description says what verbump is for: version and changelog bumps for repos, with one package or several.

## [0.1.0] - 2026-11-09

### Added
- `verbump.toml` declares packages: a path, the files that carry its version, extra `watch` paths and `exclude` globs, and its tag format (`{name}/v{version}` by default).
- `verbump plan` and `verbump apply` release every package whose files changed since its last tag. The bump comes from `--bump`, from trunk-semver's outputs (`--previous` and `--version-from`), or from a branch name. `--exact NAME=X.Y.Z` and `--release-branch release/<name>/X.Y.Z` set an exact version.
- The changelog's "Unreleased" notes become the version's section; with no notes, the section lists the commits that touched the package.
- `verbump tag`, `verbump notes`, `verbump set`, `verbump check`, `verbump status` and `verbump init`.
- Known version files: `pyproject.toml`, `Cargo.toml`, `package.json`, `Chart.yaml`, `VERSION`, `*.py` (`__version__`), `*.csproj` and `*.props`; anything else takes a `pattern`.
- A release workflow that runs trunk-semver, then verbump on this repo.
