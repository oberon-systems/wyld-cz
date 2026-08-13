import re
import subprocess
import sys

import pytest
from commitizen.config.base_config import BaseConfig

from wyld_cz import WyldCommitizen


def run_in_fresh_interpreter(code: str) -> None:
    """Run code in a clean interpreter, so sys.modules does not hide import issues."""
    subprocess.run([sys.executable, '-c', code], check=True)


@pytest.mark.parametrize(
    'code',
    [
        'import wyld_cz; assert wyld_cz.WyldCommitizen',
        'import wyld_cz.base; assert wyld_cz.base.WyldCommitizen',
        'import commitizen; import wyld_cz; assert wyld_cz.WyldCommitizen',
    ],
)
def test_import_order_does_not_break_plugin_discovery(code: str) -> None:
    run_in_fresh_interpreter(code)


def test_plugin_is_registered() -> None:
    run_in_fresh_interpreter(
        'from commitizen.cz import registry; '
        "assert 'wyld_cz' in registry, sorted(registry)",
    )


@pytest.fixture(name='cz')
def cz_fixture() -> WyldCommitizen:
    return WyldCommitizen(BaseConfig())


def test_message_without_optional_parts(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'fix',
        'scope': 'sso/users',
        'subject': 'update jwt signature check',
    }

    assert cz.message(answers) == '[fix][sso/users]: update jwt signature check'


def test_message_with_body_and_issue(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'feat',
        'scope': 'sso',
        'subject': 'add jwt support',
        'body': 'Add JWT support for the auth backend.',
        'issue': 'https://example.com/issue/342',
    }

    message = cz.message(answers)

    assert message.splitlines() == [
        '[feat][sso]: add jwt support',
        '',
        '    Add JWT support for the auth backend.',
        '',
        '    https://example.com/issue/342',
    ]


def test_questions_offer_known_types(cz: WyldCommitizen) -> None:
    questions = {question['name']: question for question in cz.questions()}
    types = {choice['value'] for choice in questions['type']['choices']}

    assert types == {'fix', 'feat', 'build', 'docs', 'refactor'}
    assert set(questions) == {'type', 'scope', 'subject', 'body', 'issue'}


def test_schema_pattern_matches_generated_message(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'refactor',
        'scope': 'env',
        'subject': 'update development env',
    }

    assert re.match(cz.schema_pattern(), cz.message(answers))


@pytest.mark.parametrize(
    'message',
    [
        'broken message',
        '[unknown][env]: update development env',
        '[fix]: update development env',
        '[fix][env] update development env',
    ],
)
def test_schema_pattern_rejects_invalid_messages(cz: WyldCommitizen, message: str) -> None:
    assert not re.match(cz.schema_pattern(), message)
