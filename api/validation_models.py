"""
Pydantic models for Slice 5.7 API validation.

Defines request and response schemas for public endpoints:
- POST /api/v1/simulate
- GET /api/v1/scenarios
- GET /api/v1/data/ingestion-health
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


# ==================== Enums ====================

class ScenarioType(str, Enum):
    """Scenario type enumeration."""
    BASELINE = "baseline"
    CUSTOM = "custom"
    RECOMMENDED = "recommended"
    HEALTHCARE = "healthcare"
    TAX_REFORM = "tax_reform"
    SPENDING = "spending"
    SPENDING_REFORM = "spending_reform"
    SOCIAL_SECURITY = "social_security"
    COMBINED = "combined"


class SortBy(str, Enum):
    """Scenario sort options."""
    NAME = "name"
    CREATED_AT = "created_at"
    IMPACT_DEFICIT = "impact_deficit"


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class FilterType(str, Enum):
    """Scenario filter options."""
    BASELINE = "baseline"
    CUSTOM = "custom"
    RECOMMENDED = "recommended"
    ALL = "all"


class ErrorCode(str, Enum):
    """API error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    RATE_LIMITED = "RATE_LIMITED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    TIMEOUT = "TIMEOUT"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# ==================== Request Models ====================

class SimulateRequest(BaseModel):
    """Request model for POST /api/v1/simulate."""
    
    policy_name: str = Field(..., min_length=1, max_length=100, description="Policy name")
    revenue_change_pct: float = Field(..., ge=-50, le=100, description="Revenue change percentage")
    spending_change_pct: float = Field(..., ge=-50, le=100, description="Spending change percentage")
    years: int = Field(10, ge=1, le=30, description="Projection years")
    iterations: int = Field(5000, ge=100, le=50000, description="Monte Carlo iterations")
    random_seed: Optional[int] = Field(None, description="Seed for reproducibility")
    include_sensitivity: bool = Field(False, description="Include sensitivity analysis")
    
    @field_validator('policy_name')
    @classmethod
    def validate_policy_name(cls, v: str) -> str:
        """Validate policy name format (alphanumeric + spaces/hyphens)."""
        if not all(c.isalnum() or c in ' -_' for c in v):
            raise ValueError('Policy name must contain only alphanumeric, spaces, hyphens, or underscores')
        return v


class ScenariosListRequest(BaseModel):
    """Request model for GET /api/v1/scenarios (query params converted to model)."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    filter_type: FilterType = Field(FilterType.ALL, description="Scenario type filter")
    search: Optional[str] = Field(None, max_length=200, description="Search string")
    sort_by: SortBy = Field(SortBy.CREATED_AT, description="Sort field")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class IngestionHealthRequest(BaseModel):
    """Request model for GET /api/v1/data/ingestion-health (query params)."""
    
    include_history: bool = Field(False, description="Include historical data (requires auth)")


# ==================== Response Models ====================

class SimulationResults(BaseModel):
    """Simulation results sub-model."""
    
    mean_deficit: float = Field(..., description="Mean deficit (billions)")
    median_deficit: float = Field(..., description="Median deficit (billions)")
    std_dev: float = Field(..., description="Standard deviation")
    p10_deficit: float = Field(..., description="10th percentile deficit")
    p90_deficit: float = Field(..., description="90th percentile deficit")
    probability_balanced: float = Field(..., ge=0, le=1, description="Probability of balanced budget")
    confidence_bounds: List[float] = Field(..., description="[p10, p90] confidence interval")


class SensitivityParameter(BaseModel):
    """Sensitivity analysis parameter sub-model."""
    
    name: str = Field(..., description="Parameter name")
    impact_low: float = Field(..., description="Low impact estimate")
    impact_high: float = Field(..., description="High impact estimate")
    tornado_rank: int = Field(..., ge=1, description="Rank in tornado diagram")


class SensitivityAnalysis(BaseModel):
    """Sensitivity analysis sub-model."""
    
    parameters: List[SensitivityParameter] = Field(..., description="Sensitivity parameters")


class SimulationMetadata(BaseModel):
    """Metadata sub-model for simulation response."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    api_version: str = Field(..., description="API version")
    duration_ms: int = Field(..., ge=0, description="Duration in milliseconds")


class SimulateResponse(BaseModel):
    """Response model for POST /api/v1/simulate."""
    
    status: str = Field("success", description="Status")
    simulation_id: str = Field(..., description="Simulation UUID")
    policy_name: str = Field(..., description="Policy name")
    years: int = Field(..., description="Projection years")
    iterations: int = Field(..., description="Monte Carlo iterations")
    results: SimulationResults = Field(..., description="Simulation results")
    sensitivity: Optional[SensitivityAnalysis] = Field(None, description="Sensitivity analysis")
    metadata: SimulationMetadata = Field(..., description="Response metadata")


class ScenarioListItem(BaseModel):
    """Individual scenario in list response."""
    
    id: str = Field(..., description="Scenario UUID")
    name: str = Field(..., description="Scenario name")
    type: ScenarioType = Field(..., description="Scenario type")
    description: str = Field(..., description="Scenario description")
    revenue_change_pct: float = Field(..., description="Revenue change %")
    spending_change_pct: float = Field(..., description="Spending change %")
    projected_deficit: float = Field(..., description="Projected deficit (billions)")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Creator (username or 'system')")
    is_public: bool = Field(..., description="Is publicly visible")
    tags: List[str] = Field(default_factory=list, description="Tags")


class PaginationInfo(BaseModel):
    """Pagination info sub-model."""
    
    page: int = Field(..., ge=1, description="Current page")
    per_page: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=1, description="Total pages")


class ScenariosListMetadata(BaseModel):
    """Metadata for scenarios list response."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    api_version: str = Field(..., description="API version")


class ScenariosListResponse(BaseModel):
    """Response model for GET /api/v1/scenarios."""
    
    status: str = Field("success", description="Status")
    scenario_count: int = Field(..., ge=0, description="Total scenarios available")
    returned_count: int = Field(..., ge=0, description="Scenarios in this page")
    pagination: PaginationInfo = Field(..., description="Pagination info")
    scenarios: List[ScenarioListItem] = Field(..., description="Scenarios list")
    metadata: ScenariosListMetadata = Field(..., description="Response metadata")


class IngestionInfo(BaseModel):
    """Ingestion status sub-model."""
    
    data_source: str = Field(..., description="Data source (CBO|Treasury|OMB|cache)")
    is_live: bool = Field(..., description="Is live fetch")
    freshness_hours: float = Field(..., ge=0, description="Freshness in hours")
    cache_age_hours: float = Field(..., ge=0, description="Cache age in hours")
    last_updated: datetime = Field(..., description="Last update timestamp")
    fetched_at: datetime = Field(..., description="Fetch timestamp")


class ValidationInfo(BaseModel):
    """Validation status sub-model."""
    
    schema_valid: bool = Field(..., description="Is schema valid")
    checksum: str = Field(..., description="Data checksum (SHA256)")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class IngestionMetrics(BaseModel):
    """Ingestion metrics sub-model."""
    
    data_points_ingested: int = Field(..., ge=0, description="Number of data points")
    schema_version: str = Field(..., description="Schema version")


class HistoryEntry(BaseModel):
    """Historical data entry sub-model."""
    
    timestamp: datetime = Field(..., description="Entry timestamp")
    checksum: str = Field(..., description="Data checksum")
    is_live: bool = Field(..., description="Was live fetch")
    schema_valid: bool = Field(..., description="Was schema valid")


class IngestionHealthMetadata(BaseModel):
    """Metadata for ingestion health response."""
    
    api_version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Response timestamp")


class IngestionHealthResponse(BaseModel):
    """Response model for GET /api/v1/data/ingestion-health."""
    
    status: str = Field("success", description="Status")
    ingestion: IngestionInfo = Field(..., description="Ingestion info")
    validation: ValidationInfo = Field(..., description="Validation info")
    metrics: IngestionMetrics = Field(..., description="Metrics")
    history: Optional[List[HistoryEntry]] = Field(None, description="Historical data (if requested)")
    metadata: IngestionHealthMetadata = Field(..., description="Response metadata")


# ==================== Error Models ====================

class FieldError(BaseModel):
    """Field validation error."""
    
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Submitted value")


class ErrorDetails(BaseModel):
    """Error details sub-model."""
    
    field_errors: List[FieldError] = Field(default_factory=list, description="Field validation errors")


class ErrorMetadata(BaseModel):
    """Metadata for error response."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request UUID (for tracing)")
    api_version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    status: str = Field("error", description="Status")
    error_code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: ErrorDetails = Field(default_factory=ErrorDetails, description="Error details")
    metadata: ErrorMetadata = Field(..., description="Response metadata")


# ==================== Helper Functions ====================

def create_error_response(
    error_code: ErrorCode,
    message: str,
    request_id: str,
    api_version: str = "1.0",
    field_errors: Optional[List[FieldError]] = None,
) -> ErrorResponse:
    """Create a standard error response."""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=ErrorDetails(field_errors=field_errors or []),
        metadata=ErrorMetadata(
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            api_version=api_version,
        ),
    )
