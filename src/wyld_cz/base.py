from collections.abc import Mapping
from typing import Any

from commitizen.cz.base import BaseCommitizen
from commitizen.defaults import MINOR, PATCH
from commitizen.question import CzQuestion

from .utils import fmt_body

COMMIT_TYPES = {
    'fix': 'A bug fix',
    'feat': 'A new feature',
    'build': 'Changes with ci/cd',
    'docs': 'Documentation only changes',
    'refactor': 'Code change that neither fixes a bug nor adds a feature',
}

CHANGE_TYPES = {
    'feat': 'Features',
    'fix': 'Bug Fixes',
    'refactor': 'Refactor',
    'build': 'Build',
    'docs': 'Documentation',
}

TYPES_RE = '|'.join(COMMIT_TYPES)


class WyldCommitizen(BaseCommitizen):
    """
    Provide custom commitezen templates.
    """

    # Only the subject line is a changelog entry, the indented body is not.
    changelog_pattern = rf'^\[({TYPES_RE})\]'
    commit_parser = (
        rf'^\[(?P<change_type>{TYPES_RE})\]'
        r'\[(?P<scope>[^\]]+)\]: (?P<message>.*)'
    )
    change_type_map = CHANGE_TYPES
    change_type_order = list(CHANGE_TYPES.values())

    # `find_increment` matches the first group of bump_pattern against bump_map.
    bump_pattern = changelog_pattern
    bump_map = {
        r'^feat': MINOR,
        r'^fix': PATCH,
        r'^refactor': PATCH,
    }
    bump_map_major_version_zero = bump_map

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
        message = (
            f"[{answers['type']}]"
            f"[{answers['scope']}]: "
            f"{answers['subject']}"
        )

        if answers.get('body'):
            message += fmt_body(answers['body'])

        if answers.get('issue'):
            message += f"\n\n    {answers['issue']}"

        return message

    def example(self) -> str:
        """Provide an example to help understand the style (OPTIONAL)

        Used by `cz example`.
        """
        return """
        [fix][sso/users]: update jwt signature check

                Update JWT signature validation check for
                prevent weak security issues.

                issue: https://exmple.com/issue/342
        """

    def schema(self) -> str:
        """Show the schema used (OPTIONAL)

        Used by `cz schema`.
        """
        return """
            [<type>][<scope>]: <subject>

                [body]

                [issue]
        """

    def schema_pattern(self) -> str:
        """Regex matching the schema, used by `cz check`."""
        return rf'^\[({TYPES_RE})\]\[[^\]]+\]: .+'

    def info(self) -> str:
        """Explanation of the commit rules. (OPTIONAL)

        Used by `cz info`.
        """
        return """
        <TYPE>
        Change type, e.g. fix, or feature.
        <SCOPE>
        Subsystem or module.
        <SUBJECT>
        Short info about change.
        [BODY]
        Long description.
        [ISSUE]
        Link to issue.
        """
