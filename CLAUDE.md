# wyld-cz

A commitizen plugin providing the `[type][scope]: subject` commit style.
Package lives in `src/wyld_cz/`, exposed through the entry point
`commitizen.plugin -> wyld_cz = wyld_cz.base:WyldCommitizen`. Build backend is `uv_build`.

## Commit style used by this repo (and enforced by the plugin)

```text
[fix][sso/users]: update jwt signature check

    Body paragraphs are indented by four spaces and wrapped by fmt_body()
    in src/wyld_cz/utils.py, which keeps blank lines as paragraph breaks.
    Its width is the one `git log` shows, 80: git prepends four columns of
    its own, so the stored lines stay within 76.

    https://example.com/issue/342
```

Types live in `COMMIT_TYPES` (`src/wyld_cz/base.py`): `fix`, `feat`, `build`, `docs`, `refactor`.
Everything else — question choices, `schema_pattern`, `changelog_pattern`, `bump_pattern` —
is derived from that dict, so a new type is added in one place.

Validate a message before committing:
`cz check --commit-msg-file <file>` or `cz check --rev-range <range>`.

## The one trap: circular import on plugin discovery

`commitizen/cz/__init__.py` runs `registry = discover_plugins()` **at import time**, and
`commitizen/__init__.py` imports `commitizen.cz.base`. So any `import commitizen` loads every
installed plugin. If `wyld_cz.base` starts initializing *before* commitizen is imported, the
entry point loader re-enters the half-built module and dies with:

```text
AttributeError: partially initialized module 'wyld_cz.base' has no attribute 'WyldCommitizen'
```

That is why `src/wyld_cz/__init__.py` imports `commitizen` **before** `from .base import ...`.
Do not reorder those lines, do not "clean up" the unused import.

`tests/test_plugin.py` guards this by running each import case in a **fresh interpreter**
(`subprocess.run([sys.executable, '-c', ...])`) — inside one process `sys.modules` hides the bug.

## Plugin API expectations (commitizen >=4.9,<5)

- questions come from `commitizen.question.CzQuestion`; `commitizen.defaults.Questions` is
  deprecated and disappears in v5;
- `schema_pattern()` is abstract since 4.10 — without it the class cannot be instantiated;
- `changelog_pattern` is applied with `re.match` to the **whole** commit message, so anchor it
  at the subject line; commitizen then parses the subject *and every body paragraph* with
  `commit_parser`, which is why the parser must not match indented body text (otherwise every
  body line becomes its own changelog entry);
- `find_increment` matches **group(1)** of `bump_pattern` against the keys of `bump_map`;
- `major_version_zero: true` in `.cz.yaml` means `bump_map_major_version_zero` must be set too.

## Dev environment

```bash
pip install -r requirements.txt   # includes `-e .`, run from the repo root
pytest -q
pre-commit run --all-files
```

Never pin `wyld-cz` itself in `requirements.txt`: it pulls the released wheel from PyPI,
whose dependency pin then fights the local one, and the dev env cannot be built for a version
that is not published yet.

Style notes that the hooks enforce: single quotes (`double-quote-string-fixer`), trailing
commas, flake8 allows 120 columns but **pylint only 100**.

## Release

```bash
make bump                     # increment is detected from commit types, no --increment needed
git push origin main
git push origin <tag>         # tags are lightweight, --follow-tags will not send them
PYPI_TOKEN=pypi-... make publish
```

- `make` on its own prints the version and every target; `make publish` refuses to run
  without `PYPI_TOKEN`, rebuilds `dist/` from scratch and uploads only the current version,
  so the artifacts of older releases lying around in `dist/` are never re-uploaded;
- `uv` is not a dependency of the dev env, install it separately — `make build` says so;
- the version lives only in `pyproject.toml` (`version_provider: pep621` in `.cz.yaml`);
- `allowed_prefixes` in `.cz.yaml` lists `bump:` so `cz check --rev-range` (and the
  `commitizen-branch` pre-push hook) accepts commitizen's own bump commit;
- `md_style.rb` excludes MD002/MD024 because the generated `CHANGELOG.md` starts at a `##`
  header and repeats section names across releases — otherwise markdownlint fails the bump commit;
- the pre-commit hook config carries `additional_dependencies: [wyld-cz]`, without it the
  hook environment cannot resolve `name: wyld_cz` from `.cz.yaml`.
