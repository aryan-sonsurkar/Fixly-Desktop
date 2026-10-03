"""Document ↔ subject/course association (P0.2 Loop 2).

- upload without subject keeps working, unlinked
- upload with own subject persists the link
- malformed subject id rejected, nothing stored
- other-user subject rejected (ownership check), nothing stored
- update can set / keep the link; bad values rejected before any write
"""

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.services.document_service import DocumentService

SUBJECT_ID = "11111111-2222-3333-4444-555555555555"
OTHER_SUBJECT_ID = "99999999-8888-7777-6666-555555555555"


class _FakeFile:
    def __init__(self, name="notes.pdf", body=b"%PDF-1.4 fake"):
        self.filename = name
        self._body = body

    async def read(self):
        return self._body


def _service(monkeypatch, tmp_path):
    svc = DocumentService(access_token="tok")
    monkeypatch.setattr("app.services.document_service.UPLOAD_DIR", str(tmp_path))
    return svc


@pytest.mark.asyncio
async def test_upload_without_subject_stays_unlinked(monkeypatch, tmp_path):
    svc = _service(monkeypatch, tmp_path)
    seen = {}

    async def fake_create(user_id, payload):
        seen.update(payload)
        return {"id": "d1", **payload}

    monkeypatch.setattr(svc.repository, "create_document", fake_create)
    out = await svc.upload_document("u1", _FakeFile())
    assert out["id"] == "d1"
    assert seen.get("subject_id") is None


@pytest.mark.asyncio
async def test_upload_with_own_subject_links(monkeypatch, tmp_path):
    svc = _service(monkeypatch, tmp_path)
    seen = {}

    async def fake_create(user_id, payload):
        seen.update(payload)
        return {"id": "d1", **payload}

    async def fake_get_subject(subject_id, user_id):
        assert user_id == "u1"
        assert subject_id == SUBJECT_ID
        return {"id": SUBJECT_ID, "user_id": "u1", "name": "DBMS"}

    monkeypatch.setattr(svc.repository, "create_document", fake_create)
    monkeypatch.setattr(svc.subject_service, "get_subject", fake_get_subject)
    out = await svc.upload_document("u1", _FakeFile(), subject_id=SUBJECT_ID)
    assert out["subject_id"] == SUBJECT_ID


@pytest.mark.asyncio
async def test_upload_with_malformed_subject_rejected(monkeypatch, tmp_path):
    svc = _service(monkeypatch, tmp_path)
    called = []

    async def fake_create(user_id, payload):
        called.append(payload)
        return {"id": "d1"}

    monkeypatch.setattr(svc.repository, "create_document", fake_create)
    with pytest.raises(ValidationError):
        await svc.upload_document("u1", _FakeFile(), subject_id="not-a-uuid")
    assert called == []


@pytest.mark.asyncio
async def test_upload_with_other_user_subject_rejected(monkeypatch, tmp_path):
    svc = _service(monkeypatch, tmp_path)
    called = []

    async def fake_create(user_id, payload):
        called.append(payload)
        return {"id": "d1"}

    async def fake_get_subject(subject_id, user_id):
        raise NotFoundError("Subject not found")

    monkeypatch.setattr(svc.repository, "create_document", fake_create)
    monkeypatch.setattr(svc.subject_service, "get_subject", fake_get_subject)
    with pytest.raises(NotFoundError):
        await svc.upload_document("u1", _FakeFile(), subject_id=OTHER_SUBJECT_ID)
    assert called == []


@pytest.mark.asyncio
async def test_update_association_validated(monkeypatch):
    svc = DocumentService(access_token="tok")
    writes = []

    async def fake_get_document(document_id, user_id):
        return {"id": document_id, "user_id": user_id, "original_name": "n.pdf"}

    async def fake_update(document_id, user_id, updates):
        writes.append(dict(updates))
        return {"id": document_id, **updates}

    async def fake_get_subject(subject_id, user_id):
        assert (subject_id, user_id) == (SUBJECT_ID, "u1")
        return {"id": SUBJECT_ID, "user_id": "u1", "name": "DBMS"}

    async def fake_get_subject_missing(subject_id, user_id):
        raise NotFoundError("Subject not found")

    monkeypatch.setattr(svc.repository, "get_document", fake_get_document)
    monkeypatch.setattr(svc.repository, "update_document", fake_update)
    monkeypatch.setattr(svc.subject_service, "get_subject", fake_get_subject)
    out = await svc.update_document("d1", "u1", {"subject_id": SUBJECT_ID})
    assert out["subject_id"] == SUBJECT_ID
    assert writes and writes[0]["subject_id"] == SUBJECT_ID

    # unrelated fields still pass through untouched
    out2 = await svc.update_document("d1", "u1", {"is_favorite": True})
    assert out2["is_favorite"] is True

    # bad subject: rejected before any repository write
    writes.clear()
    monkeypatch.setattr(svc.subject_service, "get_subject", fake_get_subject_missing)
    with pytest.raises(NotFoundError):
        await svc.update_document("d1", "u1", {"subject_id": OTHER_SUBJECT_ID})
    assert writes == []
