"""v1.0.8 hotfix regression tests: email sync auth scope + stage-coded errors,
document upload validation, page-attributed extraction."""

import pytest

from app.core.exceptions import EmailSyncError
from app.services.email_service import EmailService, _classify_sync_error
from app.services.pdf_service import PDFService


def test_sync_worker_receives_user_token():
    """The sync worker must query with the user's JWT, or RLS hides every row."""
    service = EmailService(access_token="user-jwt")
    assert service.sync_worker.repository.access_token == "user-jwt"


def test_classify_sync_error_auth():
    err = _classify_sync_error(Exception("AUTHENTICATIONFAILED invalid credentials"))
    assert isinstance(err, EmailSyncError)
    assert err.error_code == "EMAIL_AUTH_FAILED"
    assert err.status_code == 502  # never 401: must not trip session refresh


def test_classify_sync_error_network():
    for msg in ["Temporary failure in name resolution", "Connection refused", "SSL: EOF"]:
        err = _classify_sync_error(OSError(msg))
        assert err.error_code == "EMAIL_PROVIDER_UNREACHABLE", msg
        assert err.status_code == 502


def test_classify_sync_error_generic():
    err = _classify_sync_error(ValueError("weird"))
    assert err.error_code == "EMAIL_FETCH_FAILED"


def test_email_sync_error_never_401():
    for code in ("EMAIL_AUTH_FAILED", "EMAIL_PROVIDER_UNREACHABLE",
                 "EMAIL_FETCH_FAILED", "EMAIL_PERSISTENCE_FAILED"):
        err = EmailSyncError("x", code=code)
        assert err.status_code != 401


class _FakeUpload:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


def _service_with_fake_repo(monkeypatch):
    from app.services.document_service import DocumentService

    svc = DocumentService(access_token="user-jwt")
    created = {}

    async def fake_create(user_id, payload):
        created.update(payload)
        created["id"] = "doc-1"
        return dict(created)

    monkeypatch.setattr(svc.repository, "create_document", fake_create)
    return svc, created


@pytest.mark.asyncio
async def test_upload_accepts_pdf(monkeypatch, tmp_path):
    svc, created = _service_with_fake_repo(monkeypatch)
    monkeypatch.setattr("app.services.document_service.UPLOAD_DIR", str(tmp_path))
    doc = await svc.upload_document("u1", _FakeUpload("DBMS Notes.pdf", b"%PDF-1.4 hello"))
    assert doc["id"] == "doc-1"
    assert doc["status"] == "pending"
    assert (tmp_path / doc["filename"]).exists()


@pytest.mark.asyncio
async def test_upload_rejects_bad_extension(monkeypatch, tmp_path):
    from app.core.exceptions import ValidationError

    svc, _ = _service_with_fake_repo(monkeypatch)
    monkeypatch.setattr("app.services.document_service.UPLOAD_DIR", str(tmp_path))
    with pytest.raises(ValidationError):
        await svc.upload_document("u1", _FakeUpload("notes.exe", b"MZ..."))


@pytest.mark.asyncio
async def test_upload_rejects_mismatched_magic(monkeypatch, tmp_path):
    from app.core.exceptions import ValidationError

    svc, _ = _service_with_fake_repo(monkeypatch)
    monkeypatch.setattr("app.services.document_service.UPLOAD_DIR", str(tmp_path))
    with pytest.raises(ValidationError):
        await svc.upload_document("u1", _FakeUpload("evil.pdf", b"<html>not a pdf"))


@pytest.mark.asyncio
async def test_upload_rejects_empty(monkeypatch, tmp_path):
    from app.core.exceptions import ValidationError

    svc, _ = _service_with_fake_repo(monkeypatch)
    monkeypatch.setattr("app.services.document_service.UPLOAD_DIR", str(tmp_path))
    with pytest.raises(ValidationError):
        await svc.upload_document("u1", _FakeUpload("empty.pdf", b""))


@pytest.mark.asyncio
async def test_chunk_pages_keep_page_numbers():
    svc = PDFService(access_token=None)
    chunks = await svc.chunk_pages([(1, "Alpha beta."), (3, "Gamma delta.")])
    assert [c["page_number"] for c in chunks] == [1, 3]
    assert [c["chunk_index"] for c in chunks] == [0, 1]


@pytest.mark.asyncio
async def test_chunk_text_empty_yields_nothing_indexable():
    svc = PDFService(access_token=None)
    assert await svc.chunk_text("") == []
    assert await svc.chunk_text("[No text layer found in PDF]") == []
