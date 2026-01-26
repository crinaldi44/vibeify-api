"""Helpers for running async code from sync contexts (eg Celery tasks).

Celery tasks here are synchronous functions, but much of the codebase uses async
SQLAlchemy + asyncpg. Calling ``asyncio.run()`` for every task creates and then
closes a new event loop each time, which can lead to:

  RuntimeError: Future attached to a different loop

because asyncpg connections in the pool are bound to the loop they were created
on. This module provides a per-process event loop that is created lazily and
reused across tasks within the same worker process.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

_loop: asyncio.AbstractEventLoop | None = None
_loop_pid: int | None = None


def _get_or_create_loop() -> asyncio.AbstractEventLoop:
    global _loop, _loop_pid
    pid = os.getpid()
    if _loop is None or _loop_pid != pid or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        _loop_pid = pid
        asyncio.set_event_loop(_loop)
    return _loop


def run(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine on the per-process event loop."""
    loop = _get_or_create_loop()
    return loop.run_until_complete(coro)

