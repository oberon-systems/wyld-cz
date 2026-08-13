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

## Contributing

This repo, so as others, using a `spellbook` developer console
https://github.com/oberon-systems/spellbook
