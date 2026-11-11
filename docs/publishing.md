# Publishing to PyPI

verbump is published on PyPI as **`verbump-cli`**, so anyone can run `uvx --from verbump-cli verbump` or `pipx install verbump-cli`; the command it installs is `verbump`. (The PyPI name `verbump` belongs to an unrelated project.)

The release workflow ([`.github/workflows/release.yml`](../.github/workflows/release.yml)) builds every release, and publishes it once the one-time setup below is done. Until then the `pypi` job is skipped, and a release only creates the tag, the GitHub release and the build artifact.

| Job | Runs when | Does |
|---|---|---|
| `build` | a release was made | checks out the release tag without the deploy key, runs `verbump check`, builds the sdist and the wheel |
| `pypi` | repository variable `PUBLISH_PYPI` is `true` | uploads them with PyPI Trusted Publishing (OIDC), in environment `pypi`. No token is stored |

Only `pypi` gets `id-token: write`. A version already on PyPI is skipped, so re-running a workflow is safe.

## One-time setup

Use the names below exactly; they are the ones the workflow expects.

### 1. The `pypi` environment

It exists already, limited to `main`. To recreate it:

```bash
gh api -X PUT repos/TheKathan/verbump/environments/pypi \
  -F 'deployment_branch_policy[protected_branches]=false' \
  -F 'deployment_branch_policy[custom_branch_policies]=true'
gh api -X POST repos/TheKathan/verbump/environments/pypi/deployment-branch-policies -f name=main -f type=branch
```

Adding yourself as a required reviewer on the environment is optional; every publish then waits for your approval.

### 2. A pending publisher on PyPI

Sign in at [pypi.org](https://pypi.org) (2FA on), open *Your account → Publishing*, and **add a new pending publisher** (GitHub tab):

- PyPI project name: `verbump-cli`
- Owner: `TheKathan`
- Repository name: `verbump`
- Workflow name: `release.yml`
- Environment name: `pypi`

The first upload creates the project and turns the pending publisher into a normal trusted publisher. No API token is needed at any point.

### 3. Switch publishing on

```bash
gh variable set PUBLISH_PYPI --body true --repo TheKathan/verbump
```

To stop publishing, set the variable to `false` or delete it. A release made before the variable was set is not published retroactively: re-run that release's workflow, or the next merged PR is the first release on PyPI.

## Check it

- the release run shows `build` and `pypi` as green (not skipped);
- `https://pypi.org/project/verbump-cli/` shows the new version and *Verified details* for the repository;
- from a clean shell, `uvx --from verbump-cli verbump --version` prints `verbump <version>`;
- [setup-verbump](https://github.com/TheKathan/setup-verbump)'s tests install the new version (its `1` and `verbump-cli>=1,<2` cases pick up any new 1.x).
