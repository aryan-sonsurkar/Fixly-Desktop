import logging
import re
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Patterns that look like secrets - redact before logging
_SECRET_PATTERNS = [
    re.compile(r"(eyJ[\w\-\.]+\.[\w\-\.]+\.[\w\-\.]+)", re.I),  # JWT
    re.compile(r"(sk-[\w\-]+)", re.I),
    re.compile(r"(Bearer\s+[\w\-\.]+)", re.I),
    re.compile(r"(supabase.*?key.*?[:=]\s*['\"]?[\w\.\-]+)", re.I),
    re.compile(r"(password\s*[:=]\s*['\"]?[^\s'\"]+)", re.I),
]


class SecretRedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pat in _SECRET_PATTERNS:
            msg = pat.sub("[REDACTED]", msg)
        # Also redact extra dict if contains sensitive keys
        if hasattr(record, "args") and isinstance(record.args, dict):
            pass
        record.msg = msg
        record.args = ()
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
    handler.addFilter(SecretRedactingFilter())

    root_logger = logging.getLogger()
    # Disable debug in production to avoid verbose errors
    level = logging.DEBUG if sys.argv[0].endswith("pytest") else logging.INFO
    # Respect ENVIRONMENT
    import os

    if os.environ.get("ENVIRONMENT") == "production":
        level = logging.WARNING
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
