from __future__ import annotations

import re

_REMOVE_C_COMMENT = r"""
    ( # String Literal
        \"(?:\\.|[^\\\"])*?\"
    )
    |
    ( # Comment
        \/\*.*?\*\/
        |
        \/\/[^\r\n]*?(?:[\r\n])
    )
    """


_REMOVE_TRAILING_COMMA = r"""
    ( # String Literal
        \"(?:\\.|[^\\\"])*?\"
    )
    | # Right Brace without Trailing Comma & Spaces
    ,\s*([\]}])
"""


_ADD_TRAILING_COMMA = r"""
    ( # String Literal
        \"(?:\\.|[^\\\"])*?\"
    )
    | # Don't match opening braces to avoid {,}
    ((?<=\")|[^,\[{\s])
    (?=\s*([\]}]))
"""


def _remove_c_comment(text: str) -> str:
    if text[-1] != "\n":
        text = text + "\n"
    return re.sub(
        _REMOVE_C_COMMENT,
        lambda x: x.group(1),
        text,
        flags=re.DOTALL | re.VERBOSE,
    )


def _remove_trailing_comma(text: str) -> str:
    return re.sub(
        _REMOVE_TRAILING_COMMA,
        lambda x: x.group(1) or x.group(2),
        text,
        flags=re.DOTALL | re.VERBOSE,
    )


def _add_trailing_comma(text: str) -> str:
    return re.sub(
        _ADD_TRAILING_COMMA,
        lambda x: x.group(1) or x.group(2) + ",",
        text,
        flags=re.DOTALL | re.VERBOSE,
    )
