## 0.3.1 (2026-09-18)

### Bug Fixes

- **changelog**: count only commits under changelog_paths in bump
- **issue**: added issue prefix into commit message

### Build

- **dependencies**: update commitezen and pre-commit dependencies

## 0.3.0 (2026-09-13)

### Features

- **changelog**: filter changelog by paths and publish to pypi from ci

## 0.2.2 (2026-08-26)

### Features

- **bump**: remove non-ascii symbols from commit message
- **ai**: added agents settings

### Build

- **pre-commit**: pin file hooks to the pre-commit stage
- **make**: drive the dev and release flow from a makefile

## 0.2.1 (2026-08-14)

### Bug Fixes

- **cz/utils**: keep body paragraphs and wrap them to 80 git log columns

### Documentation

- **claude**: add repository instructions for claude code

## 0.2.0 (2026-08-14)

### Features

- **plugin**: add changelog and bump rules

### Bug Fixes

- **plugin**: fix circular import on plugin discovery

### Refactor

- **env**: update development env

### Build

- **cz**: allow the bump commit in range checks
- **markdownlint**: allow generated changelog layout
- **env**: install wyld-cz from source in dev requirements
- **.gitignore**: .spellbook.json removed

## 0.1.0 (2025-08-25)

### Features

- **init**: initial commit
