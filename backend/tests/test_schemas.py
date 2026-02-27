"""
Unit tests for Pydantic schemas — validation rules and field constraints.
"""
import pytest
from pydantic import ValidationError

from schemas.forms import FinancialRiskFormInput, UseCaseFormInput
from schemas.vendor import VendorCreate, VendorList, VendorRead


class TestUseCaseFormInput:
    def _valid_payload(self, **overrides):
        base = {
            "use_case_description": "Automate invoice processing",
            "business_justification": "Reduce manual effort by 80%",
            "data_types_involved": ["PII", "financial"],
            "estimated_users": 150,
            "alternatives_considered": "Evaluated three other vendors",
            "reviewer_name": "Jane Smith",
            "recommendation": "PROCEED",
        }
        return {**base, **overrides}

    def test_valid_minimal(self):
        form = UseCaseFormInput(**self._valid_payload())
        assert form.recommendation == "PROCEED"
        assert form.notes is None

    def test_valid_with_notes(self):
        form = UseCaseFormInput(**self._valid_payload(notes="Review again in Q3"))
        assert form.notes == "Review again in Q3"

    def test_both_recommendation_values(self):
        for rec in ("PROCEED", "DO_NOT_PROCEED"):
            form = UseCaseFormInput(**self._valid_payload(recommendation=rec))
            assert form.recommendation == rec

    def test_invalid_recommendation_rejected(self):
        with pytest.raises(ValidationError):
            UseCaseFormInput(**self._valid_payload(recommendation="MAYBE"))

    def test_missing_required_field_raises(self):
        payload = self._valid_payload()
        del payload["reviewer_name"]
        with pytest.raises(ValidationError):
            UseCaseFormInput(**payload)

    def test_data_types_involved_must_be_list(self):
        with pytest.raises(ValidationError):
            UseCaseFormInput(**self._valid_payload(data_types_involved="PII"))

    def test_estimated_users_must_be_int(self):
        with pytest.raises(ValidationError):
            UseCaseFormInput(**self._valid_payload(estimated_users="lots"))


class TestFinancialRiskFormInput:
    def _valid_payload(self, **overrides):
        base = {
            "financial_documents_reviewed": ["balance_sheet", "income_statement"],
            "concentration_risk_flag": False,
            "financial_stability_assessment": "STABLE",
            "reviewer_name": "John Doe",
            "recommendation": "ACCEPTABLE",
        }
        return {**base, **overrides}

    def test_valid_minimal(self):
        form = FinancialRiskFormInput(**self._valid_payload())
        assert form.financial_stability_assessment == "STABLE"
        assert form.vendor_annual_revenue is None
        assert form.conditions is None

    def test_valid_with_all_optional_fields(self):
        form = FinancialRiskFormInput(**self._valid_payload(
            vendor_annual_revenue="$50M",
            years_in_operation=12,
            contract_value="$200K",
            conditions=["Annual audit required"],
            notes="Low risk overall",
        ))
        assert form.years_in_operation == 12
        assert form.conditions == ["Annual audit required"]

    def test_all_stability_assessments(self):
        for assessment in ("STABLE", "CONCERN", "HIGH_RISK"):
            form = FinancialRiskFormInput(**self._valid_payload(
                financial_stability_assessment=assessment
            ))
            assert form.financial_stability_assessment == assessment

    def test_invalid_stability_assessment_rejected(self):
        with pytest.raises(ValidationError):
            FinancialRiskFormInput(**self._valid_payload(
                financial_stability_assessment="UNKNOWN"
            ))

    def test_all_recommendations(self):
        for rec in ("ACCEPTABLE", "ACCEPTABLE_WITH_CONDITIONS", "UNACCEPTABLE"):
            form = FinancialRiskFormInput(**self._valid_payload(recommendation=rec))
            assert form.recommendation == rec

    def test_invalid_recommendation_rejected(self):
        with pytest.raises(ValidationError):
            FinancialRiskFormInput(**self._valid_payload(recommendation="MAYBE"))

    def test_concentration_risk_rejects_non_bool_string(self):
        # Pydantic v2 coerces "yes"/"no" to bool; "maybe" is not coercible.
        with pytest.raises(ValidationError):
            FinancialRiskFormInput(**self._valid_payload(concentration_risk_flag="maybe"))


class TestVendorCreate:
    def test_minimal(self):
        v = VendorCreate(name="Test Vendor")
        assert v.name == "Test Vendor"
        assert v.website is None
        assert v.description is None

    def test_full(self):
        v = VendorCreate(
            name="Full Vendor",
            website="https://example.com",
            description="A full vendor",
        )
        assert v.website == "https://example.com"

    def test_name_required(self):
        with pytest.raises(ValidationError):
            VendorCreate()
