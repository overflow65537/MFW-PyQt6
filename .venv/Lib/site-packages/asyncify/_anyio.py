# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import partial, wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from anyio import (
    CapacityLimiter as CapacityLimiter,
    run as anyio_run,
    to_thread as to_thread,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = (
    "anyio_run",
    "asyncify",
)

P = ParamSpec("P")
T = TypeVar("T")


def asyncify(
    funk: Callable[P, T],
    *,
    abandon_on_cancel: bool = False,
    limiter: CapacityLimiter | None = None,
) -> Callable[P, Awaitable[T]]:
    """asyncify decorator/wrapper that for use w/ anyio"""

    @wraps(funk)
    async def _async_fn(*args: P.args, **kwargs: P.kwargs) -> T:
        partial_f = partial(funk, *args, **kwargs)
        return await to_thread.run_sync(
            partial_f, abandon_on_cancel=abandon_on_cancel, limiter=limiter
        )

    return _async_fn
