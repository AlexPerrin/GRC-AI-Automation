"""
Integration tests for the /vendors API routes using FastAPI TestClient.
"""
import pytest


class TestCreateVendor:
    def test_create_vendor_returns_201(self, client):
        resp = client.post("/vendors/", json={"name": "Acme Corp"})
        assert resp.status_code == 201

    def test_create_vendor_response_shape(self, client):
        resp = client.post("/vendors/", json={
            "name": "Beta Ltd",
            "website": "https://beta.example.com",
            "description": "A beta vendor",
        })
        data = resp.json()
        assert data["name"] == "Beta Ltd"
        assert data["website"] == "https://beta.example.com"
        assert data["status"] == "INTAKE"
        assert "id" in data
        assert "created_at" in data

    def test_create_vendor_defaults_to_intake(self, client):
        resp = client.post("/vendors/", json={"name": "Gamma Inc"})
        assert resp.json()["status"] == "INTAKE"

    def test_create_vendor_without_name_returns_422(self, client):
        resp = client.post("/vendors/", json={"website": "https://example.com"})
        assert resp.status_code == 422

    def test_create_multiple_vendors_get_unique_ids(self, client):
        id1 = client.post("/vendors/", json={"name": "Vendor A"}).json()["id"]
        id2 = client.post("/vendors/", json={"name": "Vendor B"}).json()["id"]
        assert id1 != id2


class TestListVendors:
    def test_list_vendors_empty(self, client):
        resp = client.get("/vendors/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["vendors"] == []
        assert data["total"] == 0

    def test_list_vendors_returns_created_vendors(self, client):
        client.post("/vendors/", json={"name": "Vendor 1"})
        client.post("/vendors/", json={"name": "Vendor 2"})

        resp = client.get("/vendors/")
        data = resp.json()
        assert data["total"] == 2
        names = {v["name"] for v in data["vendors"]}
        assert names == {"Vendor 1", "Vendor 2"}

    def test_list_vendors_pagination_skip(self, client):
        for i in range(5):
            client.post("/vendors/", json={"name": f"Vendor {i}"})

        resp = client.get("/vendors/?skip=3&limit=10")
        data = resp.json()
        assert len(data["vendors"]) == 2
        assert data["total"] == 5

    def test_list_vendors_pagination_limit(self, client):
        for i in range(5):
            client.post("/vendors/", json={"name": f"Vendor {i}"})

        resp = client.get("/vendors/?limit=2")
        data = resp.json()
        assert len(data["vendors"]) == 2
        assert data["total"] == 5


class TestGetVendor:
    def test_get_vendor_by_id(self, client):
        created = client.post("/vendors/", json={"name": "Fetch Me"}).json()
        vendor_id = created["id"]

        resp = client.get(f"/vendors/{vendor_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fetch Me"

    def test_get_vendor_not_found_returns_404(self, client):
        resp = client.get("/vendors/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestVendorNdaAndStubEndpoints:
    def test_confirm_nda_requires_legal_approved_status(self, client):
        vendor = client.post("/vendors/", json={"name": "NDA Vendor"}).json()
        resp = client.post(f"/vendors/{vendor['id']}/confirm-nda")
        # Vendor is INTAKE, not LEGAL_APPROVED — expects 400
        assert resp.status_code == 400

    def test_confirm_nda_vendor_not_found(self, client):
        resp = client.post("/vendors/99999/confirm-nda")
        assert resp.status_code == 404

    def test_confirm_nda_success_advances_to_security_review(self, client, db_session):
        from core.models import Vendor, VendorStatus
        v = Vendor(name="NDA Success Vendor", status=VendorStatus.LEGAL_APPROVED)
        db_session.add(v)
        db_session.commit()
        db_session.refresh(v)

        resp = client.post(f"/vendors/{v.id}/confirm-nda")
        assert resp.status_code == 200
        assert resp.json()["status"] == "SECURITY_REVIEW"

    def test_complete_onboarding_advances_to_onboarded(self, client, db_session):
        from core.models import Vendor, VendorStatus
        v = Vendor(name="Onboard Vendor", status=VendorStatus.FINANCIAL_APPROVED)
        db_session.add(v)
        db_session.commit()
        db_session.refresh(v)

        resp = client.post(f"/vendors/{v.id}/complete-onboarding")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ONBOARDED"

    def test_reject_vendor_sets_rejected_status(self, client):
        vendor = client.post("/vendors/", json={"name": "Reject Vendor"}).json()
        resp = client.post(
            f"/vendors/{vendor['id']}/reject",
            params={"rationale": "Not a fit"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"
