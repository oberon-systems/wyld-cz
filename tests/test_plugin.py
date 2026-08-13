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


def test_commit_parser_extracts_changelog_entry(cz: WyldCommitizen) -> None:
    parsed = re.match(cz.commit_parser, '[fix][sso/users]: update jwt signature check')

    assert parsed
    assert parsed.group('change_type') == 'fix'
    assert parsed.group('scope') == 'sso/users'
    assert parsed.group('message') == 'update jwt signature check'


def test_changelog_pattern_skips_body_and_bump_commits(cz: WyldCommitizen) -> None:
    commit = (
        '[fix][sso]: update jwt signature check\n\n'
        '    Update JWT signature validation check.\n'
    )

    assert re.match(cz.changelog_pattern, commit)
    # the indented body must not become a changelog entry on its own
    assert not re.match(cz.commit_parser, '    Update JWT signature validation check.')
    assert not re.match(cz.changelog_pattern, 'bump: version 0.1.0 -> 0.2.0')


@pytest.mark.parametrize(
    ('message', 'expected'),
    [
        ('[feat][sso]: add jwt support', 'MINOR'),
        ('[fix][sso]: update jwt signature check', 'PATCH'),
        ('[refactor][env]: update development env', 'PATCH'),
        ('[build][env]: update requirements', None),
        ('[docs][readme]: update compatibility', None),
    ],
)
def test_bump_map_covers_commit_types(
    cz: WyldCommitizen,
    message: str,
    expected: str | None,
) -> None:
    keyword = re.search(cz.bump_pattern, message).group(1)
    increments = {
        increment
        for pattern, increment in cz.bump_map.items()
        if re.match(pattern, keyword)
    }

    assert increments == ({expected} if expected else set())
