# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-09

### Added
- `verbump.toml` declares packages: a path, the files that carry its version, extra `watch` paths and `exclude` globs, and its tag format (`{name}/v{version}` by default).
- `verbump plan` and `verbump apply` release every package whose files changed since its last tag. The bump comes from `--bump`, from trunk-semver's outputs (`--previous` and `--version-from`), or from a branch name. `--exact NAME=X.Y.Z` and `--release-branch release/<name>/X.Y.Z` set an exact version.
- The changelog's "Unreleased" notes become the version's section; with no notes, the section lists the commits that touched the package.
- `verbump tag`, `verbump notes`, `verbump set`, `verbump check`, `verbump status` and `verbump init`.
- Known version files: `pyproject.toml`, `Cargo.toml`, `package.json`, `Chart.yaml`, `VERSION`, `*.py` (`__version__`), `*.csproj` and `*.props`; anything else takes a `pattern`.
- A release workflow that runs trunk-semver, then verbump on this repo.
