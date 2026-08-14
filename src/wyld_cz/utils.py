import re
import textwrap

# Blank lines separate body paragraphs, each one is wrapped on its own.
PARAGRAPH_RE = re.compile(r'\n\s*\n')


def fmt_body(
    body: str,
    width: int = 80,
    indent: str = '    ',
) -> str:
    """Format body with proper line wrapping and indentation.

    `width` is the line length as `git log` renders it: git prepends its own
    indent to every line of the message, so the stored lines are wrapped
    `len(indent)` columns shorter.
    """
    if not body:
        return ''

    paragraphs = [
        textwrap.fill(
            paragraph,
            width=width - len(indent),
            initial_indent=indent,
            subsequent_indent=indent,
        )
        for paragraph in PARAGRAPH_RE.split(body.strip())
        if paragraph.strip()
    ]

    if not paragraphs:
        return ''

    return '\n\n' + '\n\n'.join(paragraphs)
