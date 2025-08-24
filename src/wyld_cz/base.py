from commitizen.cz.base import BaseCommitizen
from commitizen.defaults import Questions

from .utils import fmt_body


class WyldCommitizen(BaseCommitizen):
    """
    Provide custom commitezen templates.
    """

    def questions(self) -> Questions:
        """Questions regarding the commit message."""
        questions = [
            {
                'type': 'list',
                'name': 'type',
                'message': 'Select the type of change:',
                'choices': [
                    {'value': 'fix', 'name': 'fix: A bug fix'},
                    {'value': 'feat', 'name': 'feat: A new feature'},
                    {'value': 'build', 'name': 'build: Changes with ci/cd'},
                    {'value': 'docs', 'name': 'docs: Documentation only changes'},
                    {
                        'value': 'refactor',
                        'name': 'refactor: Code change that neither fixes '
                                'a bug nor adds a feature',
                    },
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

    def message(self, answers: dict) -> str:
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
