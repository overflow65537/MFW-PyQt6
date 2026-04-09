# -*- coding: utf-8 -*-
"""Asyncify core"""

from __future__ import annotations

import asyncio

from asyncio import AbstractEventLoop, get_event_loop, run as asyncio_run
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
)
from functools import partial, wraps
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    ParamSpec,
    TypeGuard,
    TypeVar,
    cast,
)

if TYPE_CHECKING:  # pragma: no cover
    from anyio import CapacityLimiter
else:
    CapacityLimiter = None

__all__ = (
    "ANYIO",
    "aiorun",
    "aiorun_anyio",
    "aiorun_asyncio",
    "aiterable",
    "anyio_asyncify",
    "anyio_run",
    "asyncify",
    "await_or_return",
    "is_async",
    "run",
)
P = ParamSpec("P")
T = TypeVar("T")
T_Retval = TypeVar("T_Retval")
ANYIO = False
try:
    from asyncify._anyio import anyio_run, asyncify as anyio_asyncify

    ANYIO = True
except ImportError:  # pragma: no cover

    def anyio_asyncify(
        funk: Callable[P, T],
        *,
        abandon_on_cancel: bool = False,
        limiter: CapacityLimiter | None = None,
    ) -> Callable[P, Awaitable[T]]:
        raise ImportError("install anyio; `pip install anyio`")

    def anyio_run(  # type: ignore[misc]
        func: Callable[..., Coroutine[Any, Any, T_Retval]],
        *args: object,
        backend: str = "asyncio",
        backend_options: dict[str, Any] | None = None,
    ) -> T_Retval:
        raise ImportError("install anyio; `pip install anyio`")


def aiterable(it: Iterable[T] | AsyncIterable[T]) -> AsyncIterator[T]:
    """Convert any-iterable to an async iterator

    Examples:
        >>> from os import remove
        >>> from asyncio import run
        >>> plain_jane_list = list(range(10))
        >>> async def consume_aiterable(it):
        ...     stuff = []
        ...     async for el in aiterable(it):
        ...         stuff.append(el)
        ...     return stuff
        >>> run(consume_aiterable(plain_jane_list))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> async def async_gen():
        ...     for b in range(10):
        ...        yield b
        >>> run(consume_aiterable(async_gen()))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> class AsyncIterable:
        ...     def __aiter__(self):
        ...         return async_gen()
        >>> run(consume_aiterable(AsyncIterable()))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    """
    if isinstance(it, AsyncIterator):
        return it

    if isinstance(it, AsyncIterable):
        return it.__aiter__()

    async def gen() -> AsyncIterator[T]:  # noqa: RUF029
        for item in it:
            yield item

    return gen()


def asyncify(
    funk: Callable[P, T],
    *,
    loop: AbstractEventLoop | None = None,
    executor: Any | None = None,
) -> Callable[P, Awaitable[T]]:
    """Makes a sync function async

    Args:
        funk: Function to make into an async coroutine
        loop: Event loop in which to run/execute
        executor: Executor to with which to execute

    Returns:
        An asynchronous function

    Examples:
        >>> from asyncify import asyncify
        >>> def add(a, b):
        ...     return a + b
        >>> add(1, 5)
        6
        >>> @asyncify
        ... def add_async(a, b):
        ...     return a + b
        >>> from asyncio import run
        >>> run(add_async(1, 5))
        6

    """
    _loop = loop
    _executor = executor

    @wraps(funk)
    async def _async_funk(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """Async wrapper function

        Args:
            *args: args to pass
            loop: Event loop in which to run/execute
            executor: Executor to with which to execute
            **kwargs: keyword arguments to be passed to the wrapped function

        Returns:
            An asynchronous coroutine

        """
        loop = _loop if _loop else get_event_loop()
        pfunc: Callable[[], T] = partial(funk, *args, **kwargs)
        return await loop.run_in_executor(_executor, pfunc)

    return cast("Callable[P, Awaitable[T]]", _async_funk)


def _run(aw: Awaitable[T], *, debug: bool | None = None) -> T:
    """Run an async/awaitable function (Polyfill asyncio.run)

    Emulate `asyncio.run()` for snakes below python 3.7; `asyncio.run` was
    added in python3.7.

    Args:
        aw (Awaitable[T]): Async/awaitable function to run
        debug (Optional[bool]): If True run event loop in debug mode

    Returns:
        T: Return the result of running the async function

    Examples:
        >>> async def add(a, b):
        ...     return a + b
        ...
        >>> from asyncify.core import _run
        >>> _run(add(1, 4))
        5

    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if debug is not None:
            loop.set_debug(debug)  # pragma: no cover
        return loop.run_until_complete(aw)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def run(aw: Coroutine[Any, Any, T], *, debug: bool | None = None, **kwargs: Any) -> T:
    """Run an async/awaitable function (Polyfill asyncio.run)

    Emulate `asyncio.run()` for snakes below python 3.7; `asyncio.run` was
    added in python3.7.

    Args:
        aw (Awaitable[T]): Async/awaitable function to run
        debug (Optional[bool]): If True run event loop in debug mode
        **kwargs: keyword arguments to be passed to the wrapped function

    Returns:
        T: Return the result of running the async function

    Examples:
        >>> async def add(a, b):
        ...     return a + b
        ...
        >>> from asyncify.core import run
        >>> run(add(1, 4))
        5

    """
    return asyncio_run(aw, debug=debug)


def is_async(obj: Any) -> bool:
    """Return True if function/object is async/awaitable

    Args:
        obj: Object (probably a function) that could be async

    Returns:
        bool: True if the object is async/awaitable; False otherwise

    Examples:
        >>> from asyncify import is_async
        >>> def add(a, b): return a + b
        >>> is_async(add)
        False
        >>> async def add_(a, b): return a + b
        >>> is_async(add_)
        True

    """
    return asyncio.iscoroutinefunction(obj) or asyncio.iscoroutine(obj)


def is_coro(obj: Any) -> TypeGuard[Awaitable[Any]]:
    return asyncio.iscoroutine(obj)


async def await_or_return(obj: Awaitable[T] | T) -> T:
    """Return the result of an awaitable or return the object

    Examples:
        >>> from asyncify import await_or_return, run
        >>> def add(a, b): return a + b
        >>> run(await_or_return(add(1, 4)))
        5
        >>> async def add_(a, b): return a + b
        >>> run(await_or_return(add_(1, 4)))
        5

    """
    return cast("T", await obj if isawaitable(obj) else obj)


def aiorun_anyio(
    awaitable_or_func: Awaitable[T_Retval]
    | Callable[..., Coroutine[Any, Any, T_Retval]],
    *args: object,
    backend: str = "asyncio",
    backend_options: dict[str, Any] | None = None,
) -> T_Retval:
    """Run an async function or awaitable using anyio

    Args:
        awaitable_or_func: Function or awaitable to run
        *args: args to pass to the function
        backend: Backend to use for running the function
        backend_options: Options to pass to the backend

    Returns:
        T_Retval: Return value of the function

    """
    if is_coro(awaitable_or_func):
        if args:
            raise ValueError("args must be empty when calling a coroutine")

        def _aw() -> Coroutine[Any, Any, T_Retval]:
            return cast("Coroutine[Any, Any, T_Retval]", awaitable_or_func)

        return anyio_run(_aw, backend=backend, backend_options=backend_options)
    return anyio_run(
        cast("Callable[..., Coroutine[Any, Any, T_Retval]]", awaitable_or_func),
        *args,
        backend=backend,
        backend_options=backend_options,
    )


def aiorun_asyncio(
    awaitable_or_func: Awaitable[T_Retval]
    | Callable[..., Coroutine[Any, Any, T_Retval]],
    *args: object,
    backend: str = "asyncio",
    backend_options: dict[str, Any] | None = None,
) -> T_Retval:
    if backend != "asyncio":
        raise ValueError(
            f"anyio not installed, backend must be 'asyncio' not '{backend}'"
        )
    _backend_options = backend_options or {}
    _debug = _backend_options.get("debug", False)
    if callable(awaitable_or_func) and not asyncio.iscoroutine(awaitable_or_func):
        return asyncio_run(
            awaitable_or_func(*args),
            debug=_debug,
        )

    if args:
        raise ValueError("args must be empty when calling a coroutine")
    return asyncio_run(
        cast("Coroutine[Any, Any, T_Retval]", awaitable_or_func), debug=_debug
    )


def aiorun(
    awaitable_or_func: Awaitable[T_Retval]
    | Callable[..., Coroutine[Any, Any, T_Retval]],
    *args: object,
    backend: str = "asyncio",
    backend_options: dict[str, Any] | None = None,
) -> T_Retval:
    return (
        aiorun_asyncio(
            awaitable_or_func, *args, backend=backend, backend_options=backend_options
        )
        if not ANYIO
        else aiorun_anyio(
            awaitable_or_func, *args, backend=backend, backend_options=backend_options
        )
    )
