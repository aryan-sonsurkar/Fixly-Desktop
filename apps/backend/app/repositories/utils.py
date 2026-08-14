from typing import Any

from postgrest.exceptions import APIError


def single_or_none(builder: Any) -> dict[str, Any] | None:
    """Execute a PostgREST query as ``.single()``, returning ``None`` when no row matches.

    PostgREST raises ``APIError`` with code ``PGRST116`` when ``.single()`` matches
    zero rows. That is a genuine "not found" condition, not an error, so it is
    converted to ``None`` here. Every other error (including ``PGRST117`` for
    multiple rows) propagates unchanged so real failures are never masked as 404s.
    """
    try:
        response = builder.single().execute()
    except APIError as exc:
        if exc.code == "PGRST116":
            return None
        raise
    data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    result = data.get("data")
    return result if isinstance(result, dict) else None
