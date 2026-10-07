import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import commitizen.bump
import pytest
from commitizen.config.base_config import BaseConfig
from commitizen.git import GitCommit, get_commits

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
        '    issue: https://example.com/issue/342',
    ]


def test_message_wraps_body_to_git_log_width(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'docs',
        'scope': 'claude',
        'subject': 'add repository instructions for claude code',
        'body': (
            'Capture the plugin API traps and the release flow that are not visible '
            'from the code itself, so future sessions do not rediscover them.'
        ),
    }

    body_lines = cz.message(answers).splitlines()[2:]
    longest = max(len(line) for line in body_lines)

    assert all(line.startswith('    ') for line in body_lines)
    # `git log` indents the whole message by four more columns, 76 + 4 = 80
    assert longest <= 76
    assert longest > 72


def test_message_keeps_body_paragraphs(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'feat',
        'scope': 'sso',
        'subject': 'add jwt support',
        'body': 'Add JWT support for the auth backend.\n\nDrop the legacy session cookie.',
        'issue': 'https://example.com/issue/342',
    }

    message = cz.message(answers)

    assert message.splitlines() == [
        '[feat][sso]: add jwt support',
        '',
        '    Add JWT support for the auth backend.',
        '',
        '    Drop the legacy session cookie.',
        '',
        '    issue: https://example.com/issue/342',
    ]


def test_message_ignores_blank_body(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'fix',
        'scope': 'sso/users',
        'subject': 'update jwt signature check',
        'body': '   \n  \n',
    }

    assert cz.message(answers) == '[fix][sso/users]: update jwt signature check'


def test_message_keeps_line_breaks_inside_paragraph(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'feat',
        'scope': 'sso',
        'subject': 'add jwt support',
        'body': 'Add JWT support:\n- sign tokens\n- verify tokens\n\n\n\nDrop the cookie.',
    }

    assert cz.message(answers).splitlines() == [
        '[feat][sso]: add jwt support',
        '',
        '    Add JWT support:',
        '    - sign tokens',
        '    - verify tokens',
        '',
        '    Drop the cookie.',
    ]


def test_message_with_breaking_change(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'fix',
        'scope': 'sso',
        'subject': 'update jwt signature check',
        'body': 'Reject weak signatures.',
        'is_breaking_change': True,
        'breaking_change': 'HS256 tokens are rejected.\nReissue them with RS256.',
        'issue': 'https://example.com/issue/342',
    }

    assert cz.message(answers).splitlines() == [
        '[!][fix][sso]: update jwt signature check',
        '',
        '    Reject weak signatures.',
        '',
        '    BREAKING CHANGE:',
        '    HS256 tokens are rejected.',
        '    Reissue them with RS256.',
        '',
        '    issue: https://example.com/issue/342',
    ]


def test_message_without_breaking_change_ignores_its_text(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'fix',
        'scope': 'sso',
        'subject': 'update jwt signature check',
        'is_breaking_change': False,
    }

    assert cz.message(answers) == '[fix][sso]: update jwt signature check'


def test_questions_offer_known_types(cz: WyldCommitizen) -> None:
    questions = {question['name']: question for question in cz.questions()}
    types = {choice['value'] for choice in questions['type']['choices']}

    assert types == {'fix', 'feat', 'build', 'docs', 'refactor'}
    assert set(questions) == {
        'type',
        'scope',
        'subject',
        'body',
        'is_breaking_change',
        'breaking_change',
        'issue',
    }


def test_breaking_change_question_is_conditional_and_mandatory(cz: WyldCommitizen) -> None:
    questions = {question['name']: question for question in cz.questions()}
    breaking = questions['breaking_change']

    assert questions['body']['multiline']
    assert breaking['multiline']
    assert not breaking['when']({'is_breaking_change': False})
    assert breaking['when']({'is_breaking_change': True})
    assert breaking['validate']('HS256 tokens are rejected.') is True
    assert isinstance(breaking['validate']('  \n '), str)


def test_schema_pattern_matches_generated_message(cz: WyldCommitizen) -> None:
    answers = {
        'type': 'refactor',
        'scope': 'env',
        'subject': 'update development env',
    }

    assert re.match(cz.schema_pattern(), cz.message(answers))


@pytest.mark.parametrize(
    'body',
    [
        '\n\n    BREAKING CHANGE:\n    HS256 tokens are rejected.',
        '\n\n    Reject weak signatures.\n\nBREAKING CHANGE: HS256 tokens are rejected.',
    ],
)
def test_schema_pattern_accepts_described_breaking_change(cz: WyldCommitizen, body: str) -> None:
    assert re.match(cz.schema_pattern(), f'[!][fix][sso]: update jwt check{body}')


@pytest.mark.parametrize(
    'message',
    [
        'broken message',
        '[unknown][env]: update development env',
        '[fix]: update development env',
        '[fix][env] update development env',
        '[!][fix][env]: update development env',
        '[!][fix][env]: update development env\n\n    BREAKING CHANGE:\n',
        '[!][fix][env]: update development env\n\n    BREAKING CHANGE:\n\n    issue: 342',
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


def test_commit_parser_extracts_breaking_mark(cz: WyldCommitizen) -> None:
    parsed = re.match(cz.commit_parser, '[!][feat][sso]: drop session cookie')

    assert parsed
    assert parsed.group('breaking') == '[!]'
    assert parsed.group('change_type') == 'feat'
    assert re.match(cz.changelog_pattern, '[!][feat][sso]: drop session cookie')


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
        ('[!][fix][sso]: update jwt signature check', 'MAJOR'),
        ('[!][docs][readme]: drop compatibility', 'MAJOR'),
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


def test_breaking_change_bumps_minor_before_major_version_one(cz: WyldCommitizen) -> None:
    keyword = re.search(cz.bump_pattern, '[!][fix][sso]: update jwt check').group(1)
    increments = [
        increment
        for pattern, increment in cz.bump_map_major_version_zero.items()
        if re.match(pattern, keyword)
    ]

    assert increments == ['MINOR']


def test_bump_message_defaults_to_ascii_without_any_config():
    """A repository that sets nothing still gets `->` instead of an arrow."""
    commitizen.bump.BUMP_MESSAGE = 'untouched'
    WyldCommitizen(BaseConfig())

    assert commitizen.bump.create_commit_message('1.0.0', '1.1.0', None) == (
        'bump: version 1.0.0 -> 1.1.0'
    )


def test_a_repository_bump_message_still_wins():
    """The plugin sets a default, it does not override a configured one."""
    WyldCommitizen(BaseConfig())
    template = 'release $current_version to $new_version'

    assert commitizen.bump.create_commit_message('1.0.0', '1.1.0', template) == (
        'release 1.0.0 to 1.1.0'
    )


@pytest.fixture(name='commit_file')
def commit_file_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., str]:
    def git(*args: str) -> str:
        return subprocess.run(
            ['git', *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git('init', '-q')
    git('config', 'user.name', 'alpha')
    git('config', 'user.email', 'alpha@example.com')
    git('config', 'commit.gpgsign', 'false')
    monkeypatch.chdir(tmp_path)

    def commit(path: str, message: str = '') -> str:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(path)
        git('add', path)
        git('commit', '-q', '-m', message or f'[build][alpha]: add {path}')
        return git('rev-parse', 'HEAD')

    return commit


def test_changelog_keeps_every_commit_without_changelog_paths(cz: WyldCommitizen) -> None:
    message = {'message': 'add alpha'}

    assert cz.changelog_message_builder_hook(message, GitCommit('HEAD', 'title')) == message


def test_changelog_lists_breaking_change_in_its_own_section(cz: WyldCommitizen) -> None:
    message = {'breaking': '[!]', 'change_type': 'fix', 'scope': 'sso', 'message': 'update jwt'}
    commit = GitCommit(
        'HEAD',
        '[!][fix][sso]: update jwt',
        '    Reject weak signatures.\n\n'
        '    BREAKING CHANGE:\n    HS256 tokens are rejected,\n    reissue them.\n\n'
        '    issue: https://example.com/issue/342',
    )

    assert cz.changelog_message_builder_hook(message, commit) == [
        {'change_type': 'fix', 'scope': 'sso', 'message': 'update jwt'},
        {
            'change_type': 'breaking',
            'scope': 'sso',
            'message': 'HS256 tokens are rejected, reissue them.',
        },
    ]
    assert cz.change_type_order[0] == cz.change_type_map['breaking']


@pytest.mark.parametrize(
    ('path', 'kept'),
    [
        ('alpha/beta/image.hcl', True),
        ('alpha/README.md', True),
        ('gamma/app.py', False),
        ('alpha-notes.md', False),
    ],
)
def test_changelog_keeps_only_commits_under_changelog_paths(
    commit_file: Callable[[str], str],
    path: str,
    kept: bool,
) -> None:
    config = BaseConfig()
    config.update({'changelog_paths': ['alpha/']})
    cz = WyldCommitizen(config)
    message = {'message': f'add {path}'}

    result = cz.changelog_message_builder_hook(message, GitCommit(commit_file(path), 'title'))

    assert result == (message if kept else None)


@pytest.mark.parametrize(
    ('changelog_paths', 'expected'),
    [
        (['alpha'], 'PATCH'),
        ([], 'MINOR'),
        (['gamma'], None),
    ],
)
def test_bump_counts_only_commits_under_changelog_paths(
    commit_file: Callable[..., str],
    monkeypatch: pytest.MonkeyPatch,
    changelog_paths: list[str],
    expected: str | None,
) -> None:
    if hasattr(commitizen.bump, 'find_increment'):
        monkeypatch.setattr(commitizen.bump, 'find_increment', commitizen.bump.find_increment)
    commit_file('main/app.py', '[feat][main]: add app')
    commit_file('alpha/app.py', '[fix][alpha]: update app')
    config = BaseConfig()
    config.update({'changelog_paths': changelog_paths})
    cz = WyldCommitizen(config)

    assert next_increment(cz, get_commits()) == expected


def next_increment(cz: WyldCommitizen, commits: list[GitCommit]) -> str | None:
    """Detect the increment the way the installed commitizen does it."""
    if hasattr(commitizen.bump, 'find_increment'):
        return commitizen.bump.find_increment(
            commits,
            regex=cz.bump_pattern,
            increments_map=cz.bump_map,
        )
    # pylint: disable-next=import-outside-toplevel,no-name-in-module
    from commitizen.version_increment import VersionIncrement

    increment = VersionIncrement.get_highest_by_messages(
        (commit.message for commit in cz.filter_commits_before_bump(commits)),
        cz.bump_pattern,
        cz.bump_map,
    )
    return None if increment == VersionIncrement.NONE else str(increment)
