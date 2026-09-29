from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class CommercialLeaseFacts(BaseModel):
    # Parties
    landlord_name: str = Field(..., description="Full legal name of Landlord / Lessor (মালিক)")
    landlord_father_or_husband: Optional[str] = Field(None, description="Father's or Husband's name")
    landlord_address: str = Field(..., description="Present / Permanent Address of Landlord")
    landlord_nid_or_passport: Optional[str] = Field(None, description="Landlord NID or Passport number")

    tenant_name: str = Field(..., description="Full legal name of Tenant / Lessee (ভাড়াটিয়া)")
    tenant_father_or_husband: Optional[str] = Field(None, description="Father's or Husband's name")
    tenant_address: str = Field(..., description="Present / Permanent Address of Tenant")
    tenant_nid_or_passport: Optional[str] = Field(None, description="Tenant NID or Passport number")
    business_name: Optional[str] = Field(None, description="Name of business operating in the premises")

    # Premises Details (তফসিল)
    premises_address: str = Field(..., description="Full address of the leased shop/office")
    shop_or_unit_no: Optional[str] = Field(None, description="Shop / Unit / Suite number")
    floor_level: Optional[str] = Field(None, description="Floor level (e.g. Ground Floor, 2nd Floor)")
    approx_area_sqft: Optional[int] = Field(None, description="Approximate area in square feet")
    district: str = Field("Dhaka", description="District where premises is located")
    thana: Optional[str] = Field(None, description="Police Station / Thana")

    # Financial Terms
    monthly_rent_bdt: int = Field(..., gt=0, description="Monthly rent amount in Bangladeshi Taka (BDT)")
    security_deposit_bdt: int = Field(..., ge=0, description="Refundable security deposit / advance in BDT")
    rent_due_day_of_month: int = Field(10, ge=1, le=31, description="Day of month by which rent must be paid (e.g., 7th or 10th)")
    yearly_rent_increment_percentage: Optional[float] = Field(0.0, ge=0, le=50, description="Annual rent escalation percentage (if any)")

    # Lease Term
    duration_months: int = Field(..., gt=0, description="Total duration of lease in months (e.g. 36 for 3 years)")
    commencement_date: str = Field(..., description="Lease start date (YYYY-MM-DD or DD Month YYYY)")
    expiry_date: Optional[str] = Field(None, description="Lease expiration date")

    # Operations & Utilities
    permitted_business_type: str = Field("General Commercial / Retail", description="Permitted commercial activity")
    electricity_bill_by: str = Field("tenant", description="Who pays electricity: tenant or landlord")
    water_bill_by: str = Field("tenant", description="Who pays water: tenant or landlord")
    service_charge_bdt: Optional[int] = Field(0, description="Monthly common service charge (if any)")

    # Termination & Notice
    notice_period_months: int = Field(2, ge=1, le=12, description="Advance notice period in months for early termination")
    sublet_allowed: bool = Field(False, description="Whether sub-letting or assigning the lease is permitted")

    # Stamp Duty & Registration
    stamp_duty_borne_by: str = Field("tenant", description="Party responsible for non-judicial stamp duty")

    @field_validator("monthly_rent_bdt")
    def validate_rent(cls, v):
        if v <= 0:
            raise ValueError("Monthly rent must be greater than 0 BDT")
        return v
