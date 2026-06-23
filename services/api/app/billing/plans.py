from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import StrEnum

from app.config import Settings, get_settings
from app.constants import BillingInterval, UserPlan
from app.models import User


class PlanName(StrEnum):
    FREE = "free"
    STUDENT = "student"
    RESEARCHER = "researcher"
    LAB = "lab"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class PlanLimits:
    plan: str
    monthly_ai_file_limit: int
    monthly_ai_cost_limit_usd: float
    max_projects: int
    max_documents: int
    max_storage_mb: int
    can_use_own_api_key: bool
    can_export: bool
    can_batch_extract: bool
    team_members: int

    def to_api(self) -> dict:
        return asdict(self)


PLAN_LIMITS: dict[str, PlanLimits] = {
    PlanName.FREE.value: PlanLimits(
        plan=PlanName.FREE.value,
        monthly_ai_file_limit=10,
        monthly_ai_cost_limit_usd=5.00,
        max_projects=2,
        max_documents=50,
        max_storage_mb=500,
        can_use_own_api_key=True,
        can_export=True,
        can_batch_extract=False,
        team_members=1,
    ),
    PlanName.STUDENT.value: PlanLimits(
        plan=PlanName.STUDENT.value,
        monthly_ai_file_limit=100,
        monthly_ai_cost_limit_usd=20.00,
        max_projects=10,
        max_documents=1000,
        max_storage_mb=5000,
        can_use_own_api_key=True,
        can_export=True,
        can_batch_extract=False,
        team_members=1,
    ),
    PlanName.RESEARCHER.value: PlanLimits(
        plan=PlanName.RESEARCHER.value,
        monthly_ai_file_limit=500,
        monthly_ai_cost_limit_usd=100.00,
        max_projects=50,
        max_documents=10000,
        max_storage_mb=50000,
        can_use_own_api_key=True,
        can_export=True,
        can_batch_extract=True,
        team_members=1,
    ),
    PlanName.LAB.value: PlanLimits(
        plan=PlanName.LAB.value,
        monthly_ai_file_limit=3000,
        monthly_ai_cost_limit_usd=500.00,
        max_projects=200,
        max_documents=100000,
        max_storage_mb=500000,
        can_use_own_api_key=True,
        can_export=True,
        can_batch_extract=True,
        team_members=10,
    ),
    PlanName.ADMIN.value: PlanLimits(
        plan=PlanName.ADMIN.value,
        monthly_ai_file_limit=1000000,
        monthly_ai_cost_limit_usd=1000000.00,
        max_projects=1000000,
        max_documents=1000000,
        max_storage_mb=10000000,
        can_use_own_api_key=True,
        can_export=True,
        can_batch_extract=True,
        team_members=1000000,
    ),
}


def get_plan_limits(plan: str | None) -> PlanLimits:
    if not plan:
        return PLAN_LIMITS[PlanName.FREE.value]
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[PlanName.FREE.value])


def get_effective_plan(user: User) -> str:
    return user.plan_override or user.plan or UserPlan.FREE.value


def get_effective_plan_limits(user: User) -> PlanLimits:
    return get_plan_limits(get_effective_plan(user))


def apply_plan_to_user(user: User, plan: str) -> None:
    limits = get_plan_limits(plan)
    user.plan = limits.plan
    user.monthly_ai_file_limit = limits.monthly_ai_file_limit
    user.monthly_ai_cost_limit_usd = limits.monthly_ai_cost_limit_usd


def get_price_id_for_plan(
    plan: str,
    billing_interval: str,
    settings: Settings | None = None,
) -> str | None:
    resolved = settings or get_settings()
    plan_key = plan.lower()
    interval_key = billing_interval.lower()
    mapping = {
        (PlanName.STUDENT.value, BillingInterval.MONTHLY.value): resolved.stripe_price_student_monthly,
        (PlanName.RESEARCHER.value, BillingInterval.MONTHLY.value): resolved.stripe_price_researcher_monthly,
        (PlanName.LAB.value, BillingInterval.MONTHLY.value): resolved.stripe_price_lab_monthly,
        (PlanName.STUDENT.value, BillingInterval.YEARLY.value): resolved.stripe_price_student_yearly,
        (PlanName.RESEARCHER.value, BillingInterval.YEARLY.value): resolved.stripe_price_researcher_yearly,
        (PlanName.LAB.value, BillingInterval.YEARLY.value): resolved.stripe_price_lab_yearly,
    }
    return mapping.get((plan_key, interval_key))


def get_plan_from_stripe_price_id(price_id: str | None, settings: Settings | None = None) -> str | None:
    if not price_id:
        return None
    resolved = settings or get_settings()
    mapping = {
        resolved.stripe_price_student_monthly: PlanName.STUDENT.value,
        resolved.stripe_price_student_yearly: PlanName.STUDENT.value,
        resolved.stripe_price_researcher_monthly: PlanName.RESEARCHER.value,
        resolved.stripe_price_researcher_yearly: PlanName.RESEARCHER.value,
        resolved.stripe_price_lab_monthly: PlanName.LAB.value,
        resolved.stripe_price_lab_yearly: PlanName.LAB.value,
    }
    return mapping.get(price_id)
