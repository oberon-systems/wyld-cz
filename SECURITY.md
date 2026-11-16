# Security policy

wyld-cz is a commitizen plugin: it is loaded into every `cz` run and every
pre-commit hook environment that names it. A flaw that runs code, reads files
or reaches the network from a commit message or a `.cz.yaml` is a security
issue.

## Supported versions

Fixes go into the next release on PyPI. Older releases get none.

| Version | Supported                |
| ------- | ------------------------ |
| Newest  | Yes                      |
| Older   | No: update to the newest |

## Report a vulnerability

Do not open a public issue or pull request. Report it privately on GitHub:
the Security tab, then
[Report a vulnerability](../../security/advisories/new). The report stays
visible to you and the maintainers only, and the fix is discussed there.

Include:

- the wyld-cz and commitizen versions, or the commit;
- what an attacker needs: a crafted commit message, a branch, a `.cz.yaml`;
- the steps to reproduce it and what they reach.

## Scope

Out of scope:

- a flaw in commitizen itself: report it to
  [commitizen](https://github.com/commitizen-tools/commitizen/security);
- an attacker who already writes to the repository's `.cz.yaml` or hooks.
