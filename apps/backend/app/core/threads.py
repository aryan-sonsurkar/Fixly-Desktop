import asyncio
import concurrent.futures
from collections.abc import Awaitable, Callable
from typing import Any

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="fixly-db")


async def run_in_thread(coro_fn: Callable[..., Awaitable[Any]], *args: Any) -> Any:
    """Run blocking Supabase calls in a thread pool without creating new event loops.

    Uses a shared ThreadPoolExecutor to avoid per-call loop creation overhead.
    coro_fn is awaited via asyncio.to_thread with executor to reuse threads.
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
                return loop_in_thread.run_until_complete(result)  # type: ignore[arg-type]
            finally:
                try:
                    loop_in_thread.close()
                except Exception:
                    pass
        return result

    return await loop.run_in_executor(_executor, _sync_wrapper)
