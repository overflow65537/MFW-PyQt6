from __future__ import annotations

import copy
import io
import json
import os
import sys
import warnings
from tokenize import COMMENT, NL, STRING, TokenInfo, generate_tokens, untokenize
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    CommentsDict = dict[str, "Comments"] | dict[int, "Comments"]
    Comments = str | CommentsDict | tuple[str, CommentsDict]

_warn_skips = (os.path.dirname(__file__),)


def _make_comment(text: str, indent: int = 0) -> str:
    return "\n".join(
        " " * indent + "// " + line if line else "" for line in text.splitlines()
    )


def _get_comments(
    comments: CommentsDict | None,
    key: str | int,
) -> tuple[str | None, CommentsDict | None]:
    if comments is not None:
        cbody: Comments | None = comments.pop(key, None)  # type: ignore[arg-type]
        if isinstance(cbody, tuple):
            chead, cbody = cbody
        elif isinstance(cbody, str):
            chead = cbody
            cbody = None
        else:
            chead = None
        return chead, cbody
    return None, None


def _warn_unused(
    comments: CommentsDict | None,
    stack: list[tuple[CommentsDict | None, int | None, str | int]],
) -> None:
    if not comments:
        return
    full_key = ".".join(str(key) for _, _, key in stack[1:])
    if full_key:
        full_key += "."
    for k in comments:
        msg = f"Unused comment with key: {full_key}{k}"
        if sys.version_info >= (3, 12):
            warnings.warn(msg, stacklevel=2, skip_file_prefixes=_warn_skips)
        else:
            warnings.warn(msg, stacklevel=4)


def _add_comments(data: str, comments: Comments) -> str:
    header, cdict = _get_comments({0: copy.deepcopy(comments)}, 0)
    header = _make_comment(header) + "\n" if header else ""
    result: list[TokenInfo] = []
    stack: list[Any] = []
    line_shift = 0
    array_index: int | None = None
    key: str | int | None = None
    for token in generate_tokens(io.StringIO(data).readline):
        if (
            token.type == STRING or (array_index is not None and token.string != "]")
        ) and result[-1].type == NL:
            key = array_index if array_index is not None else json.loads(token.string)
            stack.append((cdict, array_index, key))
            comm, cdict = _get_comments(cdict, key)  # type: ignore[unused-ignore,reportGeneralTypeIssues]
            if comm:
                comm = _make_comment(comm, token.start[1])
                comm_coord = (token.start[0] + line_shift, 0)
                result.append(
                    TokenInfo(
                        COMMENT,
                        comm,
                        comm_coord,
                        comm_coord,
                        "",
                    ),
                )
                result.append(
                    TokenInfo(
                        NL,
                        "\n",
                        comm_coord,
                        comm_coord,
                        "",
                    ),
                )
                line_shift += 1

        if token.string == ",":
            _warn_unused(cdict, stack)
            cdict, array_index, key = stack.pop()
            if array_index is not None:
                array_index += 1
        elif token.string == "[":
            stack.append((cdict, array_index, key))
            array_index = 0
        elif token.string == "{":
            stack.append((cdict, array_index, key))
            array_index = None
        elif token.string in {"]", "}"}:
            _warn_unused(cdict, stack)
            cdict, array_index, key = stack.pop()
            if result[-1].type == NL and result[-2].string != ",":
                _warn_unused(cdict, stack)
                cdict, array_index, key = stack.pop()

        result.append(
            TokenInfo(
                token.type,
                token.string,
                (token.start[0] + line_shift, token.start[1]),
                (token.end[0] + line_shift, token.end[1]),
                token.line,
            ),
        )

    if stack:
        msg = "Error when adding comments to JSON"
        raise ValueError(msg)
    return header + untokenize(result)  # type: ignore[no-any-return]
