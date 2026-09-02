from app.providers.base import AIProvider, EmailProvider, SyncMessage, SyncResult
from app.providers.fixly_local import FixlyLocalProvider
from app.providers.gmail import GmailProvider
from app.providers.imap import IMAPProvider

IMAP_PROVIDERS: dict[str, type[IMAPProvider]] = {
    "gmail": IMAPProvider,
    "outlook": IMAPProvider,
    "yahoo": IMAPProvider,
    "zoho": IMAPProvider,
    "icloud": IMAPProvider,
    "other": IMAPProvider,
}

PROVIDER_REGISTRY: dict[str, type[EmailProvider]] = {
    **IMAP_PROVIDERS,
}


def get_provider(provider_type: str) -> EmailProvider:
    imap_cls = IMAP_PROVIDERS.get(provider_type)
    if imap_cls:
        return imap_cls(provider_type=provider_type)
    raise ValueError(f"Unsupported provider: {provider_type}")


__all__ = [
    "AIProvider",
    "EmailProvider",
    "FixlyLocalProvider",
    "GmailProvider",
    "IMAPProvider",
    "SyncMessage",
    "SyncResult",
    "get_provider",
    "PROVIDER_REGISTRY",
]
