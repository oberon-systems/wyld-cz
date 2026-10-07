import re
from collections.abc import Mapping, Sequence
from typing import Any

import commitizen.bump
from commitizen import git
from commitizen.config.base_config import BaseConfig
from commitizen.cz.base import BaseCommitizen
from commitizen.defaults import MAJOR, MINOR, PATCH
from commitizen.question import CzQuestion
from commitizen.version_schemes import Increment

from .utils import fmt_body

COMMIT_TYPES = {
    'fix': 'A bug fix',
    'feat': 'A new feature',
    'build': 'Changes with ci/cd',
    'docs': 'Documentation only changes',
    'refactor': 'Code change that neither fixes a bug nor adds a feature',
}

CHANGE_TYPES = {
    'breaking': 'Breaking Changes',
    'feat': 'Features',
    'fix': 'Bug Fixes',
    'refactor': 'Refactor',
    'build': 'Build',
    'docs': 'Documentation',
}

TYPES_RE = '|'.join(COMMIT_TYPES)

BREAKING_MARK = '[!]'
BREAKING_CHANGE = 'BREAKING CHANGE:'
BREAKING_RE = re.compile(
    rf'^\s*{BREAKING_CHANGE}(?P<text>.*?)(?=^\s*issue: |\Z)',
    re.MULTILINE | re.DOTALL,
)

BUMP_MESSAGE = 'bump: version $current_version -> $new_version'

# Removed in commitizen 4.19.1, which calls `filter_commits_before_bump` instead.
_find_increment = getattr(commitizen.bump, 'find_increment', None)


class WyldCommitizen(BaseCommitizen):
    """
    Provide custom commitezen templates.
    """

    # Only the subject line is a changelog entry, the indented body is not.
    changelog_pattern = rf'^(?:\[!\])?\[({TYPES_RE})\]'
    commit_parser = (
        rf'^(?P<breaking>\[!\])?\[(?P<change_type>{TYPES_RE})\]'
        r'\[(?P<scope>[^\]]+)\]: (?P<message>.*)'
    )
    change_type_map = CHANGE_TYPES
    change_type_order = list(CHANGE_TYPES.values())

    # `find_increment` matches the first group of bump_pattern against bump_map,
    # the breaking mark comes first, so it wins over the type that follows it.
    bump_pattern = rf'^\[(!|{TYPES_RE})\]'
    bump_map = {
        r'^!': MAJOR,
        r'^feat': MINOR,
        r'^fix': PATCH,
        r'^refactor': PATCH,
    }
    bump_map_major_version_zero = {**bump_map, r'^!': MINOR}

    def __init__(self, config: BaseConfig) -> None:
        super().__init__(config)
        # The plugin has no bump_message attribute, and commitizen reads
        # this global late, so a repository's own bump_message still wins.
        commitizen.bump.BUMP_MESSAGE = BUMP_MESSAGE
        # Before 4.19.1 commitizen has no hook for the commits a bump counts, and both
        # `cz bump` and `cz version --next` look this function up late.
        if _find_increment:
            commitizen.bump.find_increment = self.find_increment
        self._changed_files: dict[str, list[str]] = {}

    def _touches_paths(self, rev: str) -> bool:
        paths = [path.strip('/') for path in self.config.settings.get('changelog_paths', [])]
        if not paths:
            return True
        if rev not in self._changed_files:
            self._changed_files[rev] = git.get_filenames_in_commit(rev)
        return any(
            name == path or name.startswith(f'{path}/')
            for name in self._changed_files[rev]
            for path in paths
        )

    def find_increment(
        self,
        commits: Sequence[git.GitCommit],
        regex: str,
        increments_map: Mapping[str, str],
    ) -> Increment | None:
        """Detect the increment only from commits under `changelog_paths`, when it is set."""
        return _find_increment(
            self.filter_commits_before_bump(list(commits)),
            regex,
            increments_map,
        )

    def filter_commits_before_bump(self, commits: list[git.GitCommit]) -> list[git.GitCommit]:
        """Count only commits under `changelog_paths` in a bump, when it is set."""
        return [commit for commit in commits if self._touches_paths(commit.rev)]

    def changelog_message_builder_hook(
        self,
        message: dict[str, Any],
        commit: git.GitCommit,
    ) -> dict[str, Any] | None:
        """Drop commits that touch nothing under `changelog_paths`, when it is set.

        A breaking commit also gets an entry in the breaking changes section.
        """
        if not self._touches_paths(commit.rev):
            return None
        if not message.pop('breaking', None):
            return message
        found = BREAKING_RE.search(commit.body)
        text = ' '.join(found.group('text').split()) if found else message['message']
        return [message, {**message, 'change_type': 'breaking', 'message': text}]

    def questions(self) -> list[CzQuestion]:
        """Questions regarding the commit message."""
        questions = [
            {
                'type': 'list',
                'name': 'type',
                'message': 'Select the type of change:',
                'choices': [
                    {'value': name, 'name': f'{name}: {description}'}
                    for name, description in COMMIT_TYPES.items()
                ],
            },
            {
                'type': 'input',
                'name': 'scope',
                'message': 'What is the scope of this change (e.g. package, tools):',
            },
            {
                'type': 'input',
                'name': 'subject',
                'message': 'Write a short description:',
            },
            {
                'type': 'input',
                'name': 'body',
                'message': 'Provide a longer description (optional):',
                'multiline': True,
            },
            {
                'type': 'confirm',
                'name': 'is_breaking_change',
                'message': 'Is this a BREAKING CHANGE?',
                'default': False,
            },
            {
                'type': 'input',
                'name': 'breaking_change',
                'message': 'Describe what breaks and how to migrate:',
                'multiline': True,
                'when': lambda answers: answers.get('is_breaking_change', False),
                'validate': lambda text: bool(text.strip()) or 'Describe the breaking change',
            },
            {
                'type': 'input',
                'name': 'issue',
                'message': 'Link to issue (optional):',
            },
        ]
        return questions

    def message(self, answers: Mapping[str, Any]) -> str:
        """Generate the message with the given answers."""
        breaking = answers.get('is_breaking_change', False)
        sections = [
            f"{BREAKING_MARK if breaking else ''}"
            f"[{answers['type']}]"
            f"[{answers['scope']}]: "
            f"{answers['subject']}",
            fmt_body(answers.get('body', '')),
        ]

        if breaking:
            text = fmt_body(answers.get('breaking_change', ''))
            sections.append(f'    {BREAKING_CHANGE}\n{text}')

        if answers.get('issue'):
            sections.append(f"    issue: {answers['issue']}")

        return '\n\n'.join(section for section in sections if section)

    def example(self) -> str:
        """Provide an example to help understand the style (OPTIONAL)

        Used by `cz example`.
        """
        return """
        [!][fix][sso/users]: update jwt signature check

                Update JWT signature validation check for
                prevent weak security issues.

                BREAKING CHANGE:
                Tokens signed with HS256 are rejected now,
                reissue them with RS256.

                issue: https://exmple.com/issue/342
        """

    def schema(self) -> str:
        """Show the schema used (OPTIONAL)

        Used by `cz schema`.
        """
        return """
            [[!]][<type>][<scope>]: <subject>

                [body]

                [BREAKING CHANGE:
                <what breaks>]

                [issue]
        """

    def schema_pattern(self) -> str:
        """Regex matching the schema, used by `cz check`."""
        header = rf'\[({TYPES_RE})\]\[[^\]]+\]: .+'
        # A breaking commit must describe the break, on the same or the next line.
        return (
            rf'(?m)^(?:\[!\]{header}\n[\s\S]*?^ *{BREAKING_CHANGE}(?: *\S| *\n *\S)'
            rf'|{header})'
        )

    def info(self) -> str:
        """Explanation of the commit rules. (OPTIONAL)

        Used by `cz info`.
        """
        return """
        [!]
        Marks a breaking change, its description is mandatory.
        <TYPE>
        Change type, e.g. fix, or feature.
        <SCOPE>
        Subsystem or module.
        <SUBJECT>
        Short info about change.
        [BODY]
        Long description.
        [BREAKING CHANGE]
        What breaks and how to migrate.
        [ISSUE]
        Link to issue.
        """
