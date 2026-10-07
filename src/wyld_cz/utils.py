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
    `len(indent)` columns shorter. Line breaks typed by the user are kept,
    blank lines collapse into a single paragraph break.
    """
    if not body:
        return ''

    paragraphs = [
        '\n'.join(
            textwrap.fill(
                line,
                width=width - len(indent),
                initial_indent=indent,
                subsequent_indent=indent,
            )
            for line in paragraph.splitlines()
            if line.strip()
        )
        for paragraph in PARAGRAPH_RE.split(body.strip())
        if paragraph.strip()
    ]

    return '\n\n'.join(paragraphs)
