# Wyld Commitezen Repository

A sets of custom rules and templates for commitezen.

You can find more info about commitezen customization with
official [documentation](https://commitizen-tools.github.io/commitizen/customization/)

## Compatibility

- Python `>=3.10` (tested on 3.10 - 3.14)
- commitizen `>=4.9,<5`

The plugin uses the modern commitizen plugin API (`commitizen.question.CzQuestion`,
mandatory `schema_pattern`), so commitizen `3.x` is not supported anymore.

## Usage

Install the plugin next to commitizen and select it in `.cz.yaml`:

```yaml
commitizen:
  name: wyld_cz
```

For the `pre-commit` hook the plugin has to be available inside the hook
environment as well:

```yaml
- hooks:
  - additional_dependencies:
    - wyld-cz
    id: commitizen
  repo: https://github.com/commitizen-tools/commitizen
  rev: v4.17.0
```

### Changelog and version of one directory

A repository that releases several things from separate `.cz.yaml` files can
limit each changelog with `changelog_paths`. The paths are relative to the
repository root, and a commit that changes nothing under any of them is left
out of the changelog. Without the key every commit is kept.

```yaml
commitizen:
  name: wyld_cz
  changelog_file: CHANGELOG.md
  changelog_paths:
  - alpha
  update_changelog_on_bump: true
```

`cz bump` and `cz version --next` detect the version increment from the same
commits, so a `feat` outside these paths does not raise the minor version.

## Commit style

```text
[fix][sso/users]: update jwt signature check

    Body paragraphs are indented by four spaces and wrapped to 80 columns as
    `git log` renders them: git prepends an indent of its own, so the stored
    lines stay within 76. Blank lines are kept as paragraph breaks.

    https://example.com/issue/342
```

The known types are `fix`, `feat`, `build`, `docs` and `refactor`. `feat` bumps
the minor version, `fix` and `refactor` the patch one, the rest do not bump at
all. Validate a message before committing:

```bash
cz check --commit-msg-file <file>
cz check --rev-range <range>
```

## Development

```bash
make          # print the current version and the available targets
make install  # editable install with the dev dependencies into .venv
make test     # run the test suite
make lint     # run the pre-commit hooks over every file
```

## Release

```bash
make bump              # increment is detected from the commit types
git push origin main
git push origin <tag>  # tags are lightweight, --follow-tags skips them
```

Pushing the tag starts the `publish` workflow in
[GitHub Actions](https://docs.github.com/actions). It runs the tests on Python
3.10, 3.12 and 3.14, checks the tag against the version in `pyproject.toml`,
builds with `uv` and uploads to PyPI through
[trusted publishing](https://docs.pypi.org/trusted-publishers/). The PyPI
project needs a trusted publisher for this repository with the workflow
`publish.yml` and the environment `pypi`.

The manual upload stays as a fallback. `make publish` refuses to run without
`PYPI_TOKEN`, rebuilds `dist/` and uploads that version only; `uv` is not part
of the dev environment and has to be installed separately.

```bash
PYPI_TOKEN=pypi-... make publish
```

## Contributing

This repo, so as others, using a `spellbook` developer console
https://github.com/oberon-systems/spellbook
