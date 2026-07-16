from app.providers.base import AIProvider, EmailProvider, SyncMessage, SyncResult
from app.providers.gemini import GeminiProvider
from app.providers.gmail import GmailProvider
from app.providers.imap import IMAPProvider
from app.providers.ollama import OllamaProvider

IMAP_PROVIDERS: dict[str, type[IMAPProvider]] = {
    "outlook": IMAPProvider,
    "yahoo": IMAPProvider,
    "zoho": IMAPProvider,
    "icloud": IMAPProvider,
    "other": IMAPProvider,
}

PROVIDER_REGISTRY: dict[str, type[EmailProvider]] = {
    "gmail": GmailProvider,
    **IMAP_PROVIDERS,
}


def get_provider(provider_type: str) -> EmailProvider:
    if provider_type == "gmail":
        return GmailProvider()
    imap_cls = IMAP_PROVIDERS.get(provider_type)
    if imap_cls:
        return imap_cls(provider_type=provider_type)
    raise ValueError(f"Unsupported provider: {provider_type}")


__all__ = [
    "AIProvider",
    "EmailProvider",
    "GeminiProvider",
    "GmailProvider",
    "IMAPProvider",
    "OllamaProvider",
    "SyncMessage",
    "SyncResult",
    "get_provider",
    "PROVIDER_REGISTRY",
]
