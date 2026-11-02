"""
Travel Budget Calculation and Financial Estimation Module
Handles expense breakdown, validation, INR formatting, and comparisons.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, Optional
import re
import pandas as pd


@dataclass
class ExpenseBreakdown:
    transportation: float
    accommodation: float
    food: float
    activities: float
    miscellaneous: float
    total_estimated: float
    user_budget: float
    difference: float
    status: str  # "Within Budget" or "Exceeding Budget"
    per_person_cost: float
    per_day_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def format_inr(amount: float) -> str:
    """Format an amount into Indian Rupee (INR) currency format (e.g. ₹15,000)."""
    try:
        val = int(round(amount))
    except (ValueError, TypeError):
        return f"₹{amount}"

    s = str(abs(val))
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last3

    prefix = "-₹" if val < 0 else "₹"
    return f"{prefix}{formatted}"


def estimate_trip_budget(
    starting_location: str,
    destination: str,
    duration_days: int,
    num_travellers: int,
    transport_mode: str,
    preference: str,
    user_budget: float
) -> ExpenseBreakdown:
    """
    Deterministic baseline cost estimation based on standard Indian travel economics.
    Used for validation, demo baseline, and fallback if LLM produces incomplete numbers.
    """
    transport_mode_clean = (transport_mode or "Bus").strip().lower()
    pref_clean = (preference or "Nature").strip().lower()

    # Per person transport baseline (round trip)
    if "flight" in transport_mode_clean:
        transport_per_person = 5500.0
    elif "train" in transport_mode_clean:
        transport_per_person = 1200.0  # AC 3-tier / sleeper hybrid
    elif "car" in transport_mode_clean or "taxi" in transport_mode_clean:
        # Car hire / fuel for trip split across travellers
        transport_per_person = (3500.0 * duration_days) / max(1, num_travellers)
    elif "bus" in transport_mode_clean:
        transport_per_person = 950.0  # Semi-sleeper / Volvo
    else:  # "any" or default
        transport_per_person = 1100.0

    total_transport = round(transport_per_person * num_travellers, 2)

    # Accommodation: Rooms required = ceil(num_travellers / 2)
    rooms = max(1, (num_travellers + 1) // 2)
    # Standard quality hotel/homestay per room per night: ~₹1,800 to ₹2,500
    nights = max(1, duration_days - 1) if duration_days > 1 else 1
    nightly_room_rate = 1800.0
    total_accommodation = round(rooms * nights * nightly_room_rate, 2)

    # Food: Per person per day: ~₹500 to ₹700 (breakfast, lunch, dinner, tea)
    daily_food_per_person = 550.0
    total_food = round(daily_food_per_person * duration_days * num_travellers, 2)

    # Activities / Sightseeing entry fees per person per day
    daily_activity_per_person = 350.0 if "adventure" in pref_clean else 250.0
    total_activities = round(daily_activity_per_person * duration_days * num_travellers, 2)

    # Miscellaneous: ~8-10% buffer for local transit, water, snacks, emergency
    subtotal = total_transport + total_accommodation + total_food + total_activities
    total_misc = round(subtotal * 0.08, 2)

    total_estimated = round(
        total_transport + total_accommodation + total_food + total_activities + total_misc,
        2
    )

    diff = round(user_budget - total_estimated, 2)
    status = "Within Budget" if total_estimated <= user_budget else "Exceeding Budget"

    return ExpenseBreakdown(
        transportation=total_transport,
        accommodation=total_accommodation,
        food=total_food,
        activities=total_activities,
        miscellaneous=total_misc,
        total_estimated=total_estimated,
        user_budget=float(user_budget),
        difference=diff,
        status=status,
        per_person_cost=round(total_estimated / max(1, num_travellers), 2),
        per_day_cost=round(total_estimated / max(1, duration_days), 2),
    )


def parse_agent_budget(
    agent_output_text: str,
    fallback_breakdown: ExpenseBreakdown
) -> ExpenseBreakdown:
    """
    Parses numerical values from the Budget Estimator agent's text output.
    If parsing fails or values are missing, falls back cleanly to the baseline breakdown.
    """
    if not agent_output_text:
        return fallback_breakdown

    text = agent_output_text.replace(",", "")  # Remove comma separators

    patterns = {
        "transportation": r"(?:transport(?:ation)?|travel\s+cost)[\w\s:]*(?:₹|inr|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)",
        "accommodation": r"(?:accommodation|stay|hotel|lodging)[\w\s:]*(?:₹|inr|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)",
        "food": r"(?:food|meals?|dining)[\w\s:]*(?:₹|inr|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)",
        "activities": r"(?:activities|sightseeing|entry\s+fees?)[\w\s:]*(?:₹|inr|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)",
        "miscellaneous": r"(?:miscellaneous|misc|emergency|buffer)[\w\s:]*(?:₹|inr|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)",
        "total": r"(?:total\s+estimated|total\s+budget|total\s+cost|grand\s+total)[\w\s:]*(?:₹|inr|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)"
    }

    extracted: Dict[str, float] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                extracted[key] = float(match.group(1))
            except (ValueError, TypeError):
                pass

    # If key items were extracted, compute the final verified total
    transport = extracted.get("transportation", fallback_breakdown.transportation)
    accommodation = extracted.get("accommodation", fallback_breakdown.accommodation)
    food = extracted.get("food", fallback_breakdown.food)
    activities = extracted.get("activities", fallback_breakdown.activities)
    misc = extracted.get("miscellaneous", fallback_breakdown.miscellaneous)

    # Reconcile Total
    calculated_total = round(transport + accommodation + food + activities + misc, 2)
    # If the agent specified an explicit total close to sum, keep consistency
    agent_total = extracted.get("total", calculated_total)
    total_estimated = calculated_total if abs(agent_total - calculated_total) > 500 else agent_total

    user_budget = fallback_breakdown.user_budget
    diff = round(user_budget - total_estimated, 2)
    status = "Within Budget" if total_estimated <= user_budget else "Exceeding Budget"

    travellers = max(1, int(round(fallback_breakdown.total_estimated / max(1, fallback_breakdown.per_person_cost))))
    days = max(1, int(round(fallback_breakdown.total_estimated / max(1, fallback_breakdown.per_day_cost))))

    return ExpenseBreakdown(
        transportation=transport,
        accommodation=accommodation,
        food=food,
        activities=activities,
        miscellaneous=misc,
        total_estimated=total_estimated,
        user_budget=user_budget,
        difference=diff,
        status=status,
        per_person_cost=round(total_estimated / travellers, 2),
        per_day_cost=round(total_estimated / days, 2),
    )


def create_expense_dataframe(
    breakdown: ExpenseBreakdown,
    num_travellers: int
) -> pd.DataFrame:
    """
    Creates a structured Pandas DataFrame for presentation in Streamlit.
    """
    total = max(1.0, breakdown.total_estimated)
    data = [
        {
            "Expense Category": "🚌 Transportation",
            "Estimated Cost (INR)": format_inr(breakdown.transportation),
            "Share (%)": f"{(breakdown.transportation / total) * 100:.1f}%",
            "Per Person (INR)": format_inr(breakdown.transportation / max(1, num_travellers)),
            "Coverage Notes": "To & from starting point + local commute"
        },
        {
            "Expense Category": "🏨 Accommodation",
            "Estimated Cost (INR)": format_inr(breakdown.accommodation),
            "Share (%)": f"{(breakdown.accommodation / total) * 100:.1f}%",
            "Per Person (INR)": format_inr(breakdown.accommodation / max(1, num_travellers)),
            "Coverage Notes": "Standard hotel / homestay rooms"
        },
        {
            "Expense Category": "🍽️ Food & Dining",
            "Estimated Cost (INR)": format_inr(breakdown.food),
            "Share (%)": f"{(breakdown.food / total) * 100:.1f}%",
            "Per Person (INR)": format_inr(breakdown.food / max(1, num_travellers)),
            "Coverage Notes": "Breakfast, lunch, dinner & local street food"
        },
        {
            "Expense Category": "🎟️ Activities & Sightseeing",
            "Estimated Cost (INR)": format_inr(breakdown.activities),
            "Share (%)": f"{(breakdown.activities / total) * 100:.1f}%",
            "Per Person (INR)": format_inr(breakdown.activities / max(1, num_travellers)),
            "Coverage Notes": "Entry tickets, viewpoints, adventure guide fees"
        },
        {
            "Expense Category": "🛡️ Miscellaneous & Buffer",
            "Estimated Cost (INR)": format_inr(breakdown.miscellaneous),
            "Share (%)": f"{(breakdown.miscellaneous / total) * 100:.1f}%",
            "Per Person (INR)": format_inr(breakdown.miscellaneous / max(1, num_travellers)),
            "Coverage Notes": "Snacks, water, souvenirs, emergency contingency"
        },
        {
            "Expense Category": "💰 Total Estimated Budget",
            "Estimated Cost (INR)": format_inr(breakdown.total_estimated),
            "Share (%)": "100.0%",
            "Per Person (INR)": format_inr(breakdown.per_person_cost),
            "Coverage Notes": "Complete estimated trip cost"
        }
    ]
    return pd.DataFrame(data)


def get_cost_saving_suggestions(breakdown: ExpenseBreakdown) -> list[str]:
    """Provides actionable advice if budget is tight or exceeded."""
    suggestions = [
        "**Off-Peak Transit**: Book government state transport (MSRTC/KSRTC) or overnight semi-sleeper buses to save on night accommodation costs.",
        "**Homestays & Hostels**: Choose verified homestays or budget boutique guest houses over star hotels for authentic hospitality and 30-40% lower room tariffs.",
        "**Local Food Exploration**: Eat at popular local eateries and 'thali' joints instead of tourist-trap restaurants for richer flavors at half the price.",
        "**Combo Passes & Group Rates**: Check for combined attraction tickets or national park shared safari jeeps to reduce activity costs.",
        "**Pre-Booking**: Reserve bus tickets and rooms at least 2 weeks in advance to avoid last-minute weekend surges."
    ]
    if breakdown.status == "Exceeding Budget":
        suggestions.insert(
            0,
            f"⚠️ **Budget Adjustment Needed**: Current estimate exceeds your target budget by {format_inr(abs(breakdown.difference))}. Consider trimming accommodation tier or opting for public bus/train options."
        )
    else:
        suggestions.insert(
            0,
            f"✅ **Healthy Surplus**: You have an estimated buffer of {format_inr(breakdown.difference)} remaining within your budget for extra experiences or shopping."
        )
    return suggestions
