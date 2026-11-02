from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, TypedDict
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=8, max_length=1200)
    industry: str | None = Field(default=None, max_length=180)
    geography: str = Field(default="Global", min_length=1, max_length=120)
    depth: Literal["quick", "standard", "comprehensive"] = "standard"
    demo_mode: bool = False


class ResearchPlan(BaseModel):
    objective: str = ""
    industry: str = "Unspecified"
    geography: str = "Global"
    research_questions: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    scope_limitations: list[str] = Field(default_factory=list)


class SourceEvidence(BaseModel):
    source_id: str
    title: str
    url: HttpUrl
    publisher: str = "Unknown"
    snippet: str = ""
    extracted_text: str = ""
    published_date: str | None = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    search_query: str = ""

    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        return str(value).strip()

    @property
    def domain(self) -> str:
        return urlparse(str(self.url)).hostname or self.publisher


class CitedFinding(BaseModel):
    statement: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    qualification: str | None = None


class MarketResearchOutput(BaseModel):
    market_overview: str = "No verified market overview was produced."
    industry_trends: list[CitedFinding] = Field(default_factory=list)
    customer_demand: list[CitedFinding] = Field(default_factory=list)
    opportunities: list[CitedFinding] = Field(default_factory=list)
    challenges: list[CitedFinding] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class CompetitorProfile(BaseModel):
    name: str
    products_services: list[str] = Field(default_factory=list)
    positioning: str = "Not established from available evidence."
    pricing: str = "Not publicly verified."
    strengths: list[CitedFinding] = Field(default_factory=list)
    weaknesses: list[CitedFinding] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class CompetitorAnalysisOutput(BaseModel):
    competitors: list[CompetitorProfile] = Field(default_factory=list)
    comparison_dimensions: list[str] = Field(default_factory=list)
    comparison_notes: list[CitedFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class CustomerSegment(BaseModel):
    name: str
    description: str
    pain_points: list[CitedFinding] = Field(default_factory=list)
    purchasing_behaviour: list[CitedFinding] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class CustomerInsightsOutput(BaseModel):
    segments: list[CustomerSegment] = Field(default_factory=list)
    overall_purchasing_behaviour: list[CitedFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class SWOTOutput(BaseModel):
    strengths: list[CitedFinding] = Field(default_factory=list)
    weaknesses: list[CitedFinding] = Field(default_factory=list)
    opportunities: list[CitedFinding] = Field(default_factory=list)
    threats: list[CitedFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class FinancialOpportunity(BaseModel):
    name: str
    description: str
    revenue_model: str = "Not established."
    pricing_strategy: str = "Not established."
    estimated: bool = True
    assumptions: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def label_estimate_assumptions(self) -> "FinancialOpportunity":
        if self.estimated and not self.assumptions:
            raise ValueError("An estimated business opportunity must list its assumptions.")
        return self


class FinancialAnalysisOutput(BaseModel):
    opportunities: list[FinancialOpportunity] = Field(default_factory=list)
    revenue_models: list[str] = Field(default_factory=list)
    pricing_strategies: list[CitedFinding] = Field(default_factory=list)
    assumptions_and_limitations: list[str] = Field(default_factory=list)


class ClaimVerification(BaseModel):
    claim: str
    status: Literal["verified", "partially_verified", "unverified", "conflicting"]
    source_ids: list[str] = Field(default_factory=list)
    explanation: str = ""


class VerificationOutput(BaseModel):
    verified_claims: list[ClaimVerification] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    additional_search_queries: list[str] = Field(default_factory=list)
    coverage_score: float = Field(default=0, ge=0, le=1)
    summary: str = ""


class AgentOutputRecord(BaseModel):
    agent_name: str
    output_json: str


class ReportDraft(BaseModel):
    title: str = ""
    executive_summary: str = ""
    markdown: str = ""
    source_ids: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class FinalResearchReport(BaseModel):
    title: str
    query: str
    industry: str
    geography: str
    depth: str
    executive_summary: str
    markdown: str
    source_ids: list[str] = Field(default_factory=list)
    sources: list[SourceEvidence] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)
    demo_mode: bool = False
    coverage_score: float = Field(default=0, ge=0, le=1)
    data_gaps: list[str] = Field(default_factory=list)
    agent_outputs: list[AgentOutputRecord] = Field(default_factory=list)


class AgentEvent(BaseModel):
    agent: str
    status: Literal["running", "completed", "failed", "info"]
    message: str
    timestamp: datetime = Field(default_factory=utc_now)
    duration_seconds: float | None = None
    iteration: int = 0


class ResearchState(TypedDict, total=False):
    request: ResearchRequest
    plan: ResearchPlan
    sources: Annotated[list[SourceEvidence], operator.add]
    search_calls_used: int
    iteration_count: int
    used_queries: list[str]
    additional_queries: list[str]
    market_research: MarketResearchOutput
    competitors: CompetitorAnalysisOutput
    customers: CustomerInsightsOutput
    swot: SWOTOutput
    financial: FinancialAnalysisOutput
    verification: VerificationOutput
    report: FinalResearchReport
    events: Annotated[list[AgentEvent], operator.add]
    errors: Annotated[list[str], operator.add]
    workflow_failed: bool


def reject_unknown_citations(model: BaseModel, known_source_ids: set[str]) -> None:
    """Reject model-generated citations that did not come from retrieved web sources."""
    for item in model.model_dump(mode="python").values():
        if isinstance(item, dict):
            _validate_nested_citations(item, known_source_ids)
        elif isinstance(item, list):
            for entry in item:
                if isinstance(entry, dict):
                    _validate_nested_citations(entry, known_source_ids)


def _validate_nested_citations(value: dict[str, Any], known_source_ids: set[str]) -> None:
    cited_ids = value.get("source_ids", [])
    invalid = set(cited_ids) - known_source_ids
    if invalid:
        raise ValueError(f"Agent returned unknown source IDs: {', '.join(sorted(invalid))}")
    for child in value.values():
        if isinstance(child, dict):
            _validate_nested_citations(child, known_source_ids)
        elif isinstance(child, list):
            for entry in child:
                if isinstance(entry, dict):
                    _validate_nested_citations(entry, known_source_ids)
