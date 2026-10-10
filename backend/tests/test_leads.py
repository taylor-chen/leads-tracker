import uuid

from tests.conftest import PDF_BYTES, submit_lead


class TestCreateLead:
    def test_creates_pending_lead_and_sends_both_emails(self, client, outbox, auth_headers):
        res = submit_lead(client, email="  Grace@Example.com ")
        assert res.status_code == 201, res.text
        body = res.json()
        assert set(body) == {"id", "created_at"}  # no prospect data leaked publicly

        lead = client.get(f"/api/v1/leads/{body['id']}", headers=auth_headers).json()
        assert lead["state"] == "PENDING"
        assert lead["email"] == "grace@example.com"
        assert lead["resume"]["filename"] == "resume.pdf"
        assert lead["resume"]["content_type"] == "application/pdf"

        recipients = {m.to for m in outbox.outbox}
        assert recipients == {"grace@example.com", "intake@firm.example.com"}
        attorney_mail = next(m for m in outbox.outbox if m.to == "intake@firm.example.com")
        assert f"http://frontend.test/leads/{body['id']}" in attorney_mail.text
        assert attorney_mail.reply_to == "grace@example.com"

    def test_is_public(self, client):
        assert submit_lead(client).status_code == 201

    def test_rejects_invalid_email(self, client, outbox):
        res = submit_lead(client, email="not-an-email")
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "validation_error"
        assert outbox.outbox == []

    def test_rejects_blank_name(self, client):
        assert submit_lead(client, first_name="   ").status_code == 422

    def test_requires_resume(self, client):
        res = client.post(
            "/api/v1/leads",
            data={"first_name": "A", "last_name": "B", "email": "a@b.com"},
        )
        assert res.status_code == 422

    def test_rejects_disallowed_extension(self, client):
        res = submit_lead(client, files={"resume": ("resume.exe", b"MZ...", "application/pdf")})
        assert res.status_code == 422

    def test_rejects_content_not_matching_extension(self, client):
        res = submit_lead(client, files={"resume": ("resume.pdf", b"hello", "application/pdf")})
        assert res.status_code == 422
        assert "does not match" in res.json()["error"]["message"]

    def test_rejects_oversized_resume(self, client, settings):
        big = PDF_BYTES + b"0" * settings.max_resume_bytes
        res = submit_lead(client, files={"resume": ("resume.pdf", big, "application/pdf")})
        assert res.status_code == 413

    def test_email_failure_does_not_fail_submission(self, client, outbox, monkeypatch):
        def boom(_message):
            raise RuntimeError("SMTP down")

        monkeypatch.setattr(outbox, "send", boom)
        assert submit_lead(client).status_code == 201


class TestInternalEndpointsRequireAuth:
    def test_list_requires_auth(self, client):
        res = client.get("/api/v1/leads")
        assert res.status_code == 401
        assert res.headers["www-authenticate"] == "Bearer"

    def test_get_requires_auth(self, client):
        assert client.get(f"/api/v1/leads/{uuid.uuid4()}").status_code == 401

    def test_patch_requires_auth(self, client):
        res = client.patch(f"/api/v1/leads/{uuid.uuid4()}", json={"state": "REACHED_OUT"})
        assert res.status_code == 401

    def test_rejects_bad_token(self, client):
        res = client.get("/api/v1/leads", headers={"Authorization": "Bearer nope"})
        assert res.status_code == 401


class TestListLeads:
    def test_lists_newest_first_with_pagination(self, client, auth_headers):
        ids = [submit_lead(client, first_name=f"P{i}").json()["id"] for i in range(3)]

        page1 = client.get("/api/v1/leads?page=1&page_size=2", headers=auth_headers).json()
        page2 = client.get("/api/v1/leads?page=2&page_size=2", headers=auth_headers).json()
        assert page1["total"] == 3
        assert [lead["id"] for lead in page1["items"]] == [ids[2], ids[1]]
        assert [lead["id"] for lead in page2["items"]] == [ids[0]]

    def test_filters_by_state(self, client, auth_headers):
        a = submit_lead(client).json()["id"]
        submit_lead(client)
        client.patch(f"/api/v1/leads/{a}", json={"state": "REACHED_OUT"}, headers=auth_headers)

        reached = client.get("/api/v1/leads?state=REACHED_OUT", headers=auth_headers).json()
        pending = client.get("/api/v1/leads?state=PENDING", headers=auth_headers).json()
        assert [lead["id"] for lead in reached["items"]] == [a]
        assert pending["total"] == 1

    def test_rejects_invalid_state_filter(self, client, auth_headers):
        assert client.get("/api/v1/leads?state=BOGUS", headers=auth_headers).status_code == 422


class TestGetAndUpdateLead:
    def test_get_unknown_lead_404(self, client, auth_headers):
        res = client.get(f"/api/v1/leads/{uuid.uuid4()}", headers=auth_headers)
        assert res.status_code == 404

    def test_mark_reached_out_records_actor(self, client, auth_headers):
        lead_id = submit_lead(client).json()["id"]
        res = client.patch(
            f"/api/v1/leads/{lead_id}", json={"state": "REACHED_OUT"}, headers=auth_headers
        )
        assert res.status_code == 200, res.text
        lead = res.json()
        assert lead["state"] == "REACHED_OUT"
        assert lead["reached_out_at"] is not None
        assert lead["reached_out_by"]["email"] == "attorney@firm.example.com"

    def test_cannot_move_back_to_pending(self, client, auth_headers):
        lead_id = submit_lead(client).json()["id"]
        url = f"/api/v1/leads/{lead_id}"
        client.patch(url, json={"state": "REACHED_OUT"}, headers=auth_headers)
        res = client.patch(url, json={"state": "PENDING"}, headers=auth_headers)
        assert res.status_code == 409
        assert res.json()["error"]["code"] == "invalid_state_transition"

    def test_same_state_is_idempotent(self, client, auth_headers):
        lead_id = submit_lead(client).json()["id"]
        url = f"/api/v1/leads/{lead_id}"
        client.patch(url, json={"state": "REACHED_OUT"}, headers=auth_headers)
        res = client.patch(url, json={"state": "REACHED_OUT"}, headers=auth_headers)
        assert res.status_code == 200

    def test_download_resume(self, client, auth_headers):
        lead_id = submit_lead(client).json()["id"]
        res = client.get(f"/api/v1/leads/{lead_id}/resume", headers=auth_headers)
        assert res.status_code == 200
        assert res.content == PDF_BYTES
        assert res.headers["content-type"] == "application/pdf"
        assert 'filename="resume.pdf"' in res.headers["content-disposition"]

    def test_download_resume_requires_auth(self, client):
        lead_id = submit_lead(client).json()["id"]
        assert client.get(f"/api/v1/leads/{lead_id}/resume").status_code == 401
