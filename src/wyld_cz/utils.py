import textwrap


def fmt_body(
    body: str,
    width: int = 120,
    indent: str = '    ',
) -> str:
    """Format body with proper line wrapping and indentation."""
    if not body:
        return ''

    body = body.strip()
    wrapped = textwrap.fill(
        body,
        width=width - len(indent),
        initial_indent=indent,
        subsequent_indent=indent,
    )

    return f"\n\n{wrapped}"
