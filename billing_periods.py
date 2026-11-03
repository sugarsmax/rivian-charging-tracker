"""
Electric utility billing periods: 28th of one month through 27th of the next.

Periods are labeled by the ending month (YY-MM), matching typical utility statements.
"""

from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta

BILLING_START_DAY = 28
BILLING_END_DAY = 27


def billing_period_bounds(period_end: date) -> tuple[date, date]:
    """Inclusive bounds for a period that ends on period_end (must be day 27)."""
    if period_end.day != BILLING_END_DAY:
        raise ValueError(f"Billing period must end on day {BILLING_END_DAY}, got {period_end}")
    prev_month_anchor = period_end.replace(day=1) - relativedelta(months=1)
    first_day = date(prev_month_anchor.year, prev_month_anchor.month, BILLING_START_DAY)
    return first_day, period_end


def current_period_end(today: date) -> date:
    """End date (27th) of the billing period that contains today."""
    if today.day >= BILLING_START_DAY:
        next_month = today + relativedelta(months=1)
        return date(next_month.year, next_month.month, BILLING_END_DAY)
    return date(today.year, today.month, BILLING_END_DAY)


def last_complete_period_end(today: date) -> date:
    """End date of the most recently completed billing period."""
    end = current_period_end(today)
    _, last_day = billing_period_bounds(end)
    if today > last_day:
        return end
    return end - relativedelta(months=1)


def format_period_range(first_day: date, last_day: date) -> str:
    if first_day.year == last_day.year:
        return f"{first_day.strftime('%b %d')} – {last_day.strftime('%b %d, %Y')}"
    return f"{first_day.strftime('%b %d, %Y')} – {last_day.strftime('%b %d, %Y')}"


def build_billing_periods(today: date, count: int) -> list[dict]:
    """
    Return billing periods oldest-first.

    Each dict includes API date bounds, YY-MM label (ending month), and a display range.
    """
    current_end = current_period_end(today)
    periods: list[dict] = []
    for i in range(count - 1, -1, -1):
        end = current_end - relativedelta(months=i)
        first_day, last_day = billing_period_bounds(end)
        periods.append(
            {
                "year": end.year,
                "month": end.month,
                "first_day": first_day.strftime("%Y-%m-%d"),
                "last_day": last_day.strftime("%Y-%m-%d"),
                "label": end.strftime("%y-%m"),
                "period_range": format_period_range(first_day, last_day),
            }
        )
    return periods


def bounds_for_month_arg(year: int, month: int) -> tuple[str, str]:
    """Date range for --month YYYY-MM (billing period ending that month)."""
    end = date(year, month, BILLING_END_DAY)
    first_day, last_day = billing_period_bounds(end)
    return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")


def last_complete_bounds(today: date) -> tuple[str, str]:
    """Date range for the last complete billing period."""
    end = last_complete_period_end(today)
    first_day, last_day = billing_period_bounds(end)
    return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
