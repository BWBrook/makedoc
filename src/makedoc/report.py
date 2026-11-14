"""Warnings raised while preparing or post-processing a build.

Each build collects its own warnings through a context variable, so builds running in
different threads do not see each other's.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_collector: ContextVar[list[str] | None] = ContextVar("makedoc_warnings", default=None)


def warn(message: str) -> None:
    collected = _collector.get()
    if collected is None:
        print(f"warning: {message}", file=sys.stderr)
    else:
        collected.append(message)


@contextmanager
def collect_warnings() -> Iterator[list[str]]:
    collected: list[str] = []
    token = _collector.set(collected)
    try:
        yield collected
    finally:
        _collector.reset(token)
