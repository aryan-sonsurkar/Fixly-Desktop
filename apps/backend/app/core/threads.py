import asyncio
import concurrent.futures
from collections.abc import Callable
from typing import Any

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="fixly-db")


async def run_in_thread(coro_fn: Callable[..., Any], *args: Any) -> Any:
    """Run blocking calls in a thread pool without creating new event loops.

    Uses a shared ThreadPoolExecutor to avoid per-call loop creation overhead.
    Accepts sync or async callables: sync results are returned directly,
    awaitables are driven to completion on a loop owned by the worker thread.
    """
    loop = asyncio.get_running_loop()
    # If coro_fn is async, wrap it to run in thread via sync execution
    # For pure sync functions, execute directly in thread pool
    def _sync_wrapper() -> Any:
        import asyncio as _asyncio
        import inspect

        result = coro_fn(*args)
        if inspect.isawaitable(result):
            # Create new loop only if needed inside thread (rare) - reuse thread logic
            try:
                loop_in_thread = _asyncio.new_event_loop()
                return loop_in_thread.run_until_complete(result)
            finally:
                try:
                    loop_in_thread.close()
                except Exception:
                    pass
        return result

    return await loop.run_in_executor(_executor, _sync_wrapper)
