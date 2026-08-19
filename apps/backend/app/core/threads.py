import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Coroutine, cast


async def run_in_thread(coro_fn: Callable[..., Awaitable[Any]], *args: Any) -> Any:
    """Run an async coroutine function in a worker thread with its own event loop.

    The Supabase client is synchronous, so every DB call blocks its calling thread.
    On the single main event loop those calls serialize and stall the whole app;
    running each call in a worker thread lets independent queries execute in parallel.
    """
    return await asyncio.to_thread(_run_coro_sync, coro_fn, *args)


def _run_coro_sync(coro_fn: Callable[..., Awaitable[Any]], *args: Any) -> Any:
    coro = coro_fn(*args)
    return asyncio.run(cast(Coroutine[Any, Any, Any], coro))
