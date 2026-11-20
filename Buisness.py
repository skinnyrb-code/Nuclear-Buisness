"""
Career Venture Lab - Stage 1 Streamlit Application
Team ID: NUC-0 | Pathway: NUC-3 (Nuclear Core Systems Manufacturing & Testing Studio)
Course: AP Calculus | Challenge Level: Advanced (with Foundation & Applied modes)

Stage 1 Scope:
- Startup financing, editable inputs, and capacity/resource modeling
- Deterministic monthly ledger with Decimal money precision & duplicate-run protection
- AP Calculus Math Skills Panel (Foundation, Applied, Advanced) with linked plots & tables
- JSON snapshot export/import with team_id and state_version validation
- Sample fixture replay mode (isolated from normal mode)
- Honest placeholders for Stage 2-4 modules
"""

from __future__ import annotations

import copy
import io
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Constants & Exact Money Helpers
# ---------------------------------------------------------------------------
TWO_PLACES = Decimal("0.01")

TEAM_ID_DEFAULT = "NUC-0"
PATHWAY_ID_DEFAULT = "NUC-3"
COURSE_DEFAULT = "AP Calculus"
BUSINESS_NAME = "Nuclear Core Systems Manufacturing & Testing Studio"

DEFAULT_FIXTURE_CSV = """month,requested,capacity_override,ad_cost
2027-01,30,25,0
2027-02,33,25,100
2027-03,27,20,0
"""


def d_money(val: Any) -> Decimal:
    """Convert any numeric input to a 2-decimal USD Decimal."""
    return Decimal(str(val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def fmt_usd(val: Any) -> str:
    """Format Decimal or float as USD string."""
    d = d_money(val)
    sign = "-" if d < 0 else ""
    return f"{sign}${abs(d):,.2f}"


# ---------------------------------------------------------------------------
# Default Snapshot & Deterministic Simulation Engine
# ---------------------------------------------------------------------------
def build_initial_snapshot(
    team_id: str = TEAM_ID_DEFAULT,
    selected_level: str = "Advanced",
) -> Dict[str, Any]:
    """Create the canonical opening snapshot for NUC-3."""
    return {
        "team_id": team_id,
        "course": COURSE_DEFAULT,
        "pathway_id": PATHWAY_ID_DEFAULT,
        "business_name": BUSINESS_NAME,
        "snapshot_id": "SNAP-NUC0-V0",
        "state_version": 0,
        "simulation_date": "2027-01-01",
        "base_period": "monthly",
        "working_days": 20,
        "currency": "USD",
        "selected_level": selected_level,
        "level_by_skill": {
            "optimization_and_rates": selected_level,
        },
        "assumptions": [
            "100% fictional non-hazardous engineering simulation; no real nuclear materials or real payments.",
            "Borrowing, interest, refunds, depreciation, and sales tax are disabled (not modeled) at baseline.",
            "No backlog by default: requested demand exceeding monthly capacity is recorded as lost demand.",
            "Continuous calculus curves are displayed separately from whole-unit integer ledger transactions.",
        ],
        "sources": [
            "Career Venture Lab Student Handbook (November 2026) - Custom Pathway NUC-3 & AP Calculus Adapter",
        ],
        "offerings": [
            {
                "offering_id": "OFF-01",
                "name": "Third-Party Core Diagnostics & Safety Testing",
                "role": "primary",
                "unit": "core_test",
                "price": "100.00",
                "D0": 30,
                "active": True,
            },
            {
                "offering_id": "OFF-02",
                "name": "Proprietary Modular Core Manufacturing",
                "role": "secondary_expansion",
                "unit": "modular_core",
                "price": "0.00",
                "D0": 0,
                "active": False,
                "note": "Reserved for separate capacity/inventory tracking; disabled in Stage 1 baseline.",
            },
        ],
        "funding": {
            "owner_contribution": "10000.00",
            "equipment_assets": "4500.00",
            "pre_opening_expense": "1000.00",
            "opening_inventory": "0.00",
            "opening_cash": "4500.00",
            "starting_retained_earnings": "-1000.00",
            "loan_principal": "0.00",
            "interest_rate": "0.00",
        },
        "parameters": {
            "base_price": "100.00",
            "D0": 30,
            "staff_hours": 100.0,
            "hours_per_unit": 4.0,
            "equipment_slots": 25,
            "test_rig_minutes_available": 1000.0,
            "rig_minutes_per_test": 40.0,
            "disruption_applied": False,
        },
        "cost_lines": {
            "variable_per_unit": {
                "engineer_labor": "10.00",
                "test_consumables": "5.00",
                "site_travel": "3.00",
                "verification_report": "2.00",
            },
            "fixed_monthly": {
                "testing_bay_workspace": "200.00",
                "test_rig_calibration": "150.00",
                "compliance_insurance_assumption": "150.00",
                "simulation_software": "100.00",
            },
        },
        "balances": {
            "cash": "4500.00",
            "equipment_assets": "4500.00",
            "inventory": "0.00",
            "debt": "0.00",
            "owner_equity": "10000.00",
            "retained_earnings": "-1000.00",
        },
        "capacity": {
            "derived_capacity": 25,
            "bottleneck": "Balanced (25 units across staff, slots, and test rig)",
        },
        "processed_run_ids": [],
        "ledger": [],
        "campaigns": [],
        "decisions": [],
    }


def compute_derived_capacity(params: Dict[str, Any]) -> Tuple[int, str, Dict[str, int]]:
    """
    Deterministic NUC-3 capacity formula:
    capacity = min(floor(staff_hours / hours_per_unit), equipment_slots, floor(test_rig_minutes_available / rig_minutes_per_test))
    """
    staff_hours = float(params["staff_hours"])
    hours_per_unit = float(params["hours_per_unit"])
    equipment_slots = int(params["equipment_slots"])
    rig_minutes = float(params["test_rig_minutes_available"])
    rig_per_test = float(params["rig_minutes_per_test"])

    if hours_per_unit <= 0 or rig_per_test <= 0:
        raise ValueError("hours_per_unit and rig_minutes_per_test must be strictly positive (> 0).")
    if staff_hours < 0 or equipment_slots < 0 or rig_minutes < 0:
        raise ValueError("Resource quantities cannot be negative.")

    cap_staff = math.floor(staff_hours / hours_per_unit)
    cap_slots = equipment_slots
    cap_rig = math.floor(rig_minutes / rig_per_test)

    breakdown = {
        "staff_capacity": cap_staff,
        "equipment_slot_capacity": cap_slots,
        "test_rig_capacity": cap_rig,
    }
    cap = min(cap_staff, cap_slots, cap_rig)

    limiting = [k for k, v in breakdown.items() if v == cap]
    if len(limiting) == 3:
        bottleneck = f"All resources aligned at {cap} tests/month"
    else:
        bottleneck = f"Limited by {', '.join(limiting)} ({cap} tests/month)"

    return cap, bottleneck, breakdown


def get_cost_totals(cost_lines: Dict[str, Dict[str, str]]) -> Tuple[Decimal, Decimal]:
    """Sum variable unit costs and monthly fixed costs as exact Decimals."""
    v_total = sum((d_money(v) for v in cost_lines["variable_per_unit"].values()), Decimal("0.00"))
    f_total = sum((d_money(v) for v in cost_lines["fixed_monthly"].values()), Decimal("0.00"))
    return v_total, f_total


def run_simulation_period(
    snapshot: Dict[str, Any],
    *,
    period_label: str,
    requested_units: int,
    unit_price: Decimal | None = None,
    ad_cost: Decimal = Decimal("0.00"),
    additional_capex: Decimal = Decimal("0.00"),
    new_owner_cash: Decimal = Decimal("0.00"),
    loan_cash: Decimal = Decimal("0.00"),
    principal_repayment: Decimal = Decimal("0.00"),
    interest_expense: Decimal = Decimal("0.00"),
    run_id: str,
    capacity_override: int | None = None,
    mode: str = "normal",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Advance the simulation by one monthly period with duplicate-run protection.
    Returns (updated_snapshot, period_summary).
    """
    if requested_units < 0:
        raise ValueError("Requested units cannot be negative.")
    if ad_cost < 0 or additional_capex < 0 or new_owner_cash < 0 or loan_cash < 0:
        raise ValueError("Cash and expense inputs cannot be negative.")
    if not run_id or not run_id.strip():
        raise ValueError("A unique non-empty run_id is required.")

    if run_id in snapshot["processed_run_ids"]:
        raise ValueError(f"Duplicate run_id '{run_id}' rejected: this step was already recorded.")

    if mode == "fixture" and capacity_override is None:
        raise ValueError("Fixture mode requires an explicit capacity_override.")
    if mode == "normal" and capacity_override is not None:
        raise ValueError("Normal mode cannot mix in capacity_override.")

    updated = copy.deepcopy(snapshot)
    params = updated["parameters"]
    price = d_money(unit_price if unit_price is not None else params["base_price"])
    if price < 0:
        raise ValueError("Unit price cannot be negative.")

    if mode == "fixture":
        effective_capacity = int(capacity_override)
        bottleneck_note = f"Fixture capacity_override = {effective_capacity}"
    else:
        effective_capacity, bottleneck_note, _ = compute_derived_capacity(params)

    sold_units = min(int(requested_units), effective_capacity)
    lost_demand = max(0, int(requested_units) - sold_units)

    var_per_unit, fixed_monthly = get_cost_totals(updated["cost_lines"])
    ad_cost_d = d_money(ad_cost)
    capex_d = d_money(additional_capex)
    owner_in_d = d_money(new_owner_cash)
    loan_in_d = d_money(loan_cash)
    principal_d = d_money(principal_repayment)
    interest_d = d_money(interest_expense)

    revenue = (price * Decimal(sold_units)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    variable_expense = (var_per_unit * Decimal(sold_units)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    fixed_expense = fixed_monthly
    total_operating_expense = variable_expense + fixed_expense + ad_cost_d
    operating_profit = revenue - total_operating_expense
    net_profit = operating_profit - interest_d

    opening_cash = d_money(updated["balances"]["cash"])
    ending_cash = (
        opening_cash
        + revenue
        - variable_expense
        - fixed_expense
        - ad_cost_d
        - interest_d
        - principal_d
        - capex_d
        + owner_in_d
        + loan_in_d
    ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    if ending_cash < Decimal("0.00"):
        raise ValueError(
            f"Insufficient cash ({fmt_usd(ending_cash)}): period outflows exceed opening cash of {fmt_usd(opening_cash)}."
        )

    new_version = int(updated["state_version"]) + 1
    tx_base = f"TX-{new_version:03d}"
    campaign_id = f"CAMP-{period_label}" if ad_cost_d > 0 else None

    new_entries: List[Dict[str, Any]] = []
    if sold_units > 0 and revenue > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-REV",
                "date": f"{period_label}-28",
                "event_type": "sale",
                "category": "service_revenue",
                "amount": str(revenue),
                "quantity": sold_units,
                "unit_price": str(price),
                "offering_id": "OFF-01",
                "campaign_id": None,
                "financing_type": None,
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    if variable_expense > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-VAR",
                "date": f"{period_label}-28",
                "event_type": "expense",
                "category": "variable_operating_expense",
                "amount": str(-variable_expense),
                "quantity": sold_units,
                "unit_price": str(var_per_unit),
                "offering_id": "OFF-01",
                "campaign_id": None,
                "financing_type": None,
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    if fixed_expense > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-FIX",
                "date": f"{period_label}-28",
                "event_type": "expense",
                "category": "fixed_operating_expense",
                "amount": str(-fixed_expense),
                "quantity": 1,
                "unit_price": str(fixed_expense),
                "offering_id": "OFF-01",
                "campaign_id": None,
                "financing_type": None,
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    if ad_cost_d > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-MKT",
                "date": f"{period_label}-28",
                "event_type": "expense",
                "category": "own_marketing_expense",
                "amount": str(-ad_cost_d),
                "quantity": 1,
                "unit_price": str(ad_cost_d),
                "offering_id": "OFF-01",
                "campaign_id": campaign_id,
                "financing_type": None,
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    if capex_d > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-CAPEX",
                "date": f"{period_label}-28",
                "event_type": "capital_expenditure",
                "category": "equipment_asset_addition",
                "amount": str(-capex_d),
                "quantity": 1,
                "unit_price": str(capex_d),
                "offering_id": None,
                "campaign_id": None,
                "financing_type": "capex",
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    if loan_in_d > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-LOAN",
                "date": f"{period_label}-28",
                "event_type": "financing",
                "category": "loan_proceeds",
                "amount": str(loan_in_d),
                "quantity": 1,
                "unit_price": str(loan_in_d),
                "offering_id": None,
                "campaign_id": None,
                "financing_type": "loan_receipt",
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    if owner_in_d > 0:
        new_entries.append(
            {
                "transaction_id": f"{tx_base}-EQ",
                "date": f"{period_label}-28",
                "event_type": "financing",
                "category": "owner_contribution",
                "amount": str(owner_in_d),
                "quantity": 1,
                "unit_price": str(owner_in_d),
                "offering_id": None,
                "campaign_id": None,
                "financing_type": "equity",
                "state_version": new_version,
                "run_id": run_id,
            }
        )

    # Update balances
    updated["balances"]["cash"] = str(ending_cash)
    updated["balances"]["equipment_assets"] = str(
        (d_money(updated["balances"]["equipment_assets"]) + capex_d).quantize(TWO_PLACES)
    )
    updated["balances"]["debt"] = str(
        (d_money(updated["balances"]["debt"]) + loan_in_d - principal_d).quantize(TWO_PLACES)
    )
    updated["balances"]["owner_equity"] = str(
        (d_money(updated["balances"]["owner_equity"]) + owner_in_d).quantize(TWO_PLACES)
    )
    updated["balances"]["retained_earnings"] = str(
        (d_money(updated["balances"]["retained_earnings"]) + net_profit).quantize(TWO_PLACES)
    )

    updated["state_version"] = new_version
    updated["snapshot_id"] = f"SNAP-{updated['team_id']}-V{new_version}"
    updated["simulation_date"] = f"{period_label}-28"
    updated["capacity"] = {
        "derived_capacity": effective_capacity,
        "bottleneck": bottleneck_note,
    }
    updated["processed_run_ids"].append(run_id)
    updated["ledger"].extend(new_entries)

    summary = {
        "period": period_label,
        "mode": mode,
        "run_id": run_id,
        "state_version": new_version,
        "requested": int(requested_units),
        "capacity": effective_capacity,
        "sold": sold_units,
        "lost_demand": lost_demand,
        "unit_price": price,
        "revenue": revenue,
        "variable_expense": variable_expense,
        "fixed_expense": fixed_expense,
        "ad_cost": ad_cost_d,
        "total_expense": total_operating_expense,
        "profit": net_profit,
        "capex": capex_d,
        "closing_cash": ending_cash,
    }
    return updated, summary


def apply_calibration_disruption(snapshot: Dict[str, Any], approve_capex: bool = True) -> Dict[str, Any]:
    """
    Required NUC-3 disruption:
    Calibration source replacement cuts test_rig_minutes_available to 800 (capacity -> 20 tests)
    and optionally records a $500 capital equipment cash outflow (not operating maintenance expense).
    """
    updated = copy.deepcopy(snapshot)
    updated["parameters"]["test_rig_minutes_available"] = 800.0
    updated["parameters"]["disruption_applied"] = True
    cap, bottleneck, _ = compute_derived_capacity(updated["parameters"])
    updated["capacity"] = {"derived_capacity": cap, "bottleneck": bottleneck}

    if approve_capex:
        capex_d = Decimal("500.00")
        opening_cash = d_money(updated["balances"]["cash"])
        if opening_cash < capex_d:
            raise ValueError("Insufficient cash to fund $500 capital equipment replacement.")
        new_version = int(updated["state_version"]) + 1
        run_id = f"DISRUPTION-CAPEX-V{new_version}"
        updated["balances"]["cash"] = str((opening_cash - capex_d).quantize(TWO_PLACES))
        updated["balances"]["equipment_assets"] = str(
            (d_money(updated["balances"]["equipment_assets"]) + capex_d).quantize(TWO_PLACES)
        )
        updated["state_version"] = new_version
        updated["snapshot_id"] = f"SNAP-{updated['team_id']}-V{new_version}"
        updated["processed_run_ids"].append(run_id)
        updated["ledger"].append(
            {
                "transaction_id": f"TX-{new_version:03d}-CAPEX",
                "date": updated["simulation_date"],
                "event_type": "capital_expenditure",
                "category": "calibration_source_replacement_capex",
                "amount": str(-capex_d),
                "quantity": 1,
                "unit_price": str(capex_d),
                "offering_id": None,
                "campaign_id": None,
                "financing_type": "capex",
                "state_version": new_version,
                "run_id": run_id,
            }
        )
    return updated


def validate_and_import_snapshot(
    raw_json: str,
    expected_team_id: str,
    current_state_version: int,
) -> Dict[str, Any]:
    """
    Validate imported snapshot JSON against the Career Venture Lab data contract.
    Rejects wrong team_id, missing fields, negative quantities, or stale state_version.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON format: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Snapshot JSON must be an object.")

    required_keys = [
        "team_id",
        "course",
        "pathway_id",
        "snapshot_id",
        "state_version",
        "simulation_date",
        "parameters",
        "cost_lines",
        "balances",
        "ledger",
        "processed_run_ids",
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Snapshot rejected - missing required fields: {', '.join(missing)}")

    if data["team_id"] != expected_team_id:
        raise ValueError(
            f"Team ID mismatch: expected '{expected_team_id}', got '{data['team_id']}'. Import rejected."
        )

    imported_version = int(data["state_version"])
    if imported_version < current_state_version:
        raise ValueError(
            f"Stale state_version rejected: current state is v{current_state_version}, "
            f"imported snapshot is v{imported_version}. Reset simulation first if you intend to roll back."
        )

    params = data["parameters"]
    if float(params["staff_hours"]) < 0 or int(params["equipment_slots"]) < 0 or float(params["test_rig_minutes_available"]) < 0:
        raise ValueError("Invalid snapshot: resource quantities cannot be negative.")
    if d_money(data["balances"]["cash"]) < Decimal("0.00"):
        raise ValueError("Invalid snapshot: cash balance cannot be negative.")

    for entry in data["ledger"]:
        if int(entry.get("quantity", 0)) < 0:
            raise ValueError(f"Invalid ledger entry {entry.get('transaction_id')}: negative quantity.")

    return data


# ---------------------------------------------------------------------------
# AP Calculus Deterministic Math Engine
# ---------------------------------------------------------------------------
def compute_calculus_models(
    D0: int,
    p0: float,
    v: float,
    F: float,
    capacity: int,
) -> Dict[str, Any]:
    """
    AP Calculus Adapter calculations for NUC-3:
    q(p) = a - b*p where a = 2*D0 and b = D0/p0 on [0, 2*p0].
    """
    a = 2.0 * float(D0)
    b = float(D0) / float(p0)
    p_max = 2.0 * float(p0)

    # Unconstrained profit P(p) = (p - v)*(a - b*p) - F
    # P'(p) = a + b*v - 2*b*p
    p_unconstrained = (a + b * v) / (2.0 * b)
    q_unconstrained = max(0.0, a - b * p_unconstrained)
    profit_unconstrained = (p_unconstrained - v) * (a - b * p_unconstrained) - F

    # Constrained capacity corner: a - b*p = capacity => p_corner = (a - capacity) / b
    p_corner = (a - float(capacity)) / b

    # Candidate feasible points for constrained profit on [0, p_max]:
    candidates = [0.0, p_max]
    if 0.0 <= p_corner <= p_max:
        candidates.append(p_corner)
    if p_corner <= p_unconstrained <= p_max:
        candidates.append(p_unconstrained)

    def constrained_profit(p_val: float) -> float:
        q_raw = max(0.0, a - b * p_val)
        s_val = min(float(capacity), q_raw)
        return (p_val - v) * s_val - F

    best_p = max(candidates, key=constrained_profit)
    best_profit = constrained_profit(best_p)
    best_s = min(float(capacity), max(0.0, a - b * best_p))

    # Whole-unit rounded profit at best_p
    whole_units_at_best = math.floor(best_s)
    whole_unit_profit_at_best = (best_p - v) * whole_units_at_best - F

    # Advanced accumulation rate fixture: r(t) = 100 + 20t, c(t) = 60 + 5t on [0, 10]
    t_end = 10.0
    accum_rev = 100.0 * t_end + 10.0 * (t_end ** 2)   # 2000.00
    accum_cost = 60.0 * t_end + 2.5 * (t_end ** 2)    # 850.00
    accum_profit = accum_rev - accum_cost              # 1150.00

    return {
        "a": a,
        "b": b,
        "p_max": p_max,
        "p_unconstrained": p_unconstrained,
        "q_unconstrained": q_unconstrained,
        "profit_unconstrained": profit_unconstrained,
        "p_corner": p_corner,
        "p_corner_in_domain": 0.0 <= p_corner <= p_max,
        "best_constrained_p": best_p,
        "best_constrained_s": best_s,
        "best_constrained_profit": best_profit,
        "whole_units_at_best": whole_units_at_best,
        "whole_unit_profit_at_best": whole_unit_profit_at_best,
        "accum_rev": accum_rev,
        "accum_cost": accum_cost,
        "accum_profit": accum_profit,
    }


def load_fixture_df() -> pd.DataFrame:
    """Load sample_data/monthly_fixture.csv from disk or fallback string."""
    fixture_path = Path(__file__).parent / "sample_data" / "monthly_fixture.csv"
    if fixture_path.exists():
        return pd.read_csv(fixture_path)
    return pd.read_csv(io.StringIO(DEFAULT_FIXTURE_CSV))


def fig_to_png_bytes(fig: plt.Figure) -> bytes:
    """Render a matplotlib figure to downloadable PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Streamlit UI Application
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Career Venture Lab | NUC-3 Dashboard (Stage 1)",
        page_icon="⚛️",
        layout="wide",
    )

    if "snapshot" not in st.session_state:
        st.session_state.snapshot = build_initial_snapshot()
    if "fixture_results" not in st.session_state:
        st.session_state.fixture_results = []

    snap = st.session_state.snapshot
    params = snap["parameters"]
    var_unit, fixed_mo = get_cost_totals(snap["cost_lines"])
    cap_now, bottleneck_now, cap_breakdown = compute_derived_capacity(params)
    calc_info = compute_calculus_models(
        D0=int(params["D0"]),
        p0=float(params["base_price"]),
        v=float(var_unit),
        F=float(fixed_mo),
        capacity=cap_now,
    )

    # Top Header & Persistent Math Summary Banner
    st.title(f"⚛️ {snap['business_name']}")
    st.caption(
        f"Team ID: **{snap['team_id']}** | Pathway: **{snap['pathway_id']}** | "
        f"Snapshot: **{snap['snapshot_id']}** (State v{snap['state_version']}) | "
        f"Simulation Date: **{snap['simulation_date']}** | Stage 1 Core Build"
    )

    with st.container(border=True):
        mcol1, mcol2, mcol3, mcol4 = st.columns([1.3, 1.3, 2.2, 2.2])
        mcol1.metric("Course & Skill", "AP Calculus", "Constrained Optimization & Rates")
        mcol2.metric("Approved Level", snap["selected_level"], "Changeable in Math Panel")
        mcol3.markdown(
            f"**Demand & Profit Model:**  \n"
            f"$q(p) = {calc_info['a']:.0f} - {calc_info['b']:.2f}p$ on $0 \\le p \\le {calc_info['p_max']:.0f}$  \n"
            f"$P(p) = (p - {float(var_unit):.0f})\\min({cap_now}, q(p)) - {float(fixed_mo):.0f}$"
        )
        mcol4.markdown(
            f"**Business Question & Units:**  \n"
            f"What price $p$ (USD/test) maximizes monthly profit ($/month) given a **{cap_now}-test** lab capacity ceiling?"
        )

    # Sidebar Controls: Challenge Level & Save/Restore JSON
    with st.sidebar:
        st.header("Simulation Controls")
        new_level = st.selectbox(
            "AP Calculus Challenge Level",
            ["Foundation", "Applied", "Advanced"],
            index=["Foundation", "Applied", "Advanced"].index(snap["selected_level"]),
            help="Changing level updates the mathematical tasks, equations, plots, and evidence prompts.",
        )
        if new_level != snap["selected_level"]:
            snap["selected_level"] = new_level
            snap["level_by_skill"]["optimization_and_rates"] = new_level
            st.rerun()

        st.divider()
        st.subheader("Save / Restore JSON Snapshot")
        snap_json_str = json.dumps(snap, indent=2)
        st.download_button(
            label="⬇️ Export Snapshot JSON",
            data=snap_json_str,
            file_name=f"{snap['team_id']}_{snap['pathway_id']}_v{snap['state_version']}.json",
            mime="application/json",
            use_container_width=True,
        )

        uploaded_json = st.file_uploader("Import Snapshot JSON", type=["json"])
        if uploaded_json is not None:
            if st.button("Validate & Import JSON", use_container_width=True):
                try:
                    imported = validate_and_import_snapshot(
                        uploaded_json.getvalue().decode("utf-8"),
                        expected_team_id=snap["team_id"],
                        current_state_version=int(snap["state_version"]),
                    )
                    st.session_state.snapshot = imported
                    st.success(f"Imported {imported['snapshot_id']} (v{imported['state_version']}) successfully.")
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

        st.divider()
        if st.button("🔄 Reset to Post-Startup State (v0)", use_container_width=True):
            st.session_state.snapshot = build_initial_snapshot(
                team_id=snap["team_id"],
                selected_level=snap["selected_level"],
            )
            st.session_state.fixture_results = []
            st.rerun()

    # Navigation Tabs (Stage 1 Active + Honest Stage 2-4 Placeholders)
    tabs = st.tabs(
        [
            "1. Overview & Ledger",
            "2. Inputs, Funding & Capacity",
            "3. AP Calculus Math Panel",
            "4. Fixture Replay & Tests",
            "5. Stage 2-4 Roadmap (Not Implemented)",
        ]
    )

    # -----------------------------------------------------------------------
    # TAB 1: Overview & Dated Ledger
    # -----------------------------------------------------------------------
    with tabs[0]:
        st.subheader("Financial & Operational Snapshot")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Spendable Cash", fmt_usd(snap["balances"]["cash"]))
        c2.metric("Equipment Assets", fmt_usd(snap["balances"]["equipment_assets"]))
        c3.metric("Monthly Capacity", f"{cap_now} tests", f"Base demand: {params['D0']}")
        c4.metric(
            "Unit Contribution",
            fmt_usd(d_money(params["base_price"]) - var_unit),
            f"Price {fmt_usd(params['base_price'])} - Var {fmt_usd(var_unit)}",
        )
        c5.metric("Monthly Fixed Costs", fmt_usd(fixed_mo), "Taxes/Loans: Not modeled")

        left_col, right_col = st.columns([1.15, 1.35])
        with left_col:
            st.markdown("#### Run a Single Monthly Simulation Step (Normal Mode)")
            with st.form("run_normal_month_form"):
                period_input = st.text_input("Month Label (YYYY-MM)", value="2027-01")
                req_input = st.number_input("Requested Core Tests (units)", min_value=0, value=int(params["D0"]), step=1)
                price_input = st.number_input(
                    "Price per Core Test (USD)",
                    min_value=0.0,
                    value=float(params["base_price"]),
                    step=5.0,
                )
                ad_input = st.number_input("Approved Own-Business Campaign Spend (USD)", min_value=0.0, value=0.0, step=25.0)
                run_id_input = st.text_input(
                    "Unique Run ID (prevents duplicate execution)",
                    value=f"RUN-{period_input}-V{snap['state_version'] + 1}",
                )
                submitted = st.form_submit_button("Approve & Advance Simulation (1 Month)")
                if submitted:
                    try:
                        updated_snap, summary = run_simulation_period(
                            snap,
                            period_label=period_input.strip(),
                            requested_units=int(req_input),
                            unit_price=d_money(price_input),
                            ad_cost=d_money(ad_input),
                            run_id=run_id_input.strip(),
                            mode="normal",
                        )
                        st.session_state.snapshot = updated_snap
                        st.success(
                            f"Recorded {summary['period']}: Sold {summary['sold']}/{summary['requested']} tests "
                            f"(Lost demand: {summary['lost_demand']}), Profit {fmt_usd(summary['profit'])}, "
                            f"Closing Cash {fmt_usd(summary['closing_cash'])}."
                        )
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

        with right_col:
            st.markdown("#### Balance Check & Active Assumptions")
            bal = snap["balances"]
            total_assets = d_money(bal["cash"]) + d_money(bal["equipment_assets"]) + d_money(bal["inventory"])
            total_liab_eq = d_money(bal["debt"]) + d_money(bal["owner_equity"]) + d_money(bal["retained_earnings"])
            bal_df = pd.DataFrame(
                [
                    {"Account": "Spendable Cash", "Side": "Asset", "Balance (USD)": fmt_usd(bal["cash"])},
                    {"Account": "Equipment Assets (Test Rigs)", "Side": "Asset", "Balance (USD)": fmt_usd(bal["equipment_assets"])},
                    {"Account": "Debt / Loans", "Side": "Liability", "Balance (USD)": fmt_usd(bal["debt"])},
                    {"Account": "Owner Contribution", "Side": "Equity", "Balance (USD)": fmt_usd(bal["owner_equity"])},
                    {"Account": "Retained Earnings", "Side": "Equity", "Balance (USD)": fmt_usd(bal["retained_earnings"])},
                ]
            )
            st.dataframe(bal_df, use_container_width=True, hide_index=True)
            st.info(
                f"**Accounting Check:** Total Assets = **{fmt_usd(total_assets)}** | "
                f"Liabilities + Equity = **{fmt_usd(total_liab_eq)}** "
                f"({'Reconciled' if total_assets == total_liab_eq else 'Out of balance'})"
            )

        st.divider()
        st.subheader("Dated Event Ledger (Immutable Transaction History)")
        if not snap["ledger"]:
            st.info("No monthly transactions recorded yet. Run a month above or replay the fixture in Tab 4.")
        else:
            ledger_df = pd.DataFrame(snap["ledger"])
            st.dataframe(ledger_df, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Download Ledger CSV",
                data=ledger_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{snap['team_id']}_ledger_v{snap['state_version']}.csv",
                mime="text/csv",
            )

    # -----------------------------------------------------------------------
    # TAB 2: Inputs, Funding & Capacity
    # -----------------------------------------------------------------------
    with tabs[1]:
        st.subheader("Startup Financing, Editable Costs & Capacity Constraints")
        st.caption(
            "Note: Startup equipment ($4,500) is a capital asset and is NOT expensed again in monthly profit. "
            "Borrowing, interest, refunds, depreciation, and sales tax are disabled (not modeled) at baseline."
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Resource & Capacity Parameters")
            with st.form("capacity_params_form"):
                new_p0 = st.number_input("Base Price p0 (USD/test)", min_value=1.0, value=float(params["base_price"]), step=5.0)
                new_d0 = st.number_input("Baseline Monthly Demand D0 (tests)", min_value=0, value=int(params["D0"]), step=1)
                new_staff = st.number_input("Engineering Staff Hours / Month", min_value=0.0, value=float(params["staff_hours"]), step=4.0)
                new_hpu = st.number_input("Productive Hours / Test", min_value=0.5, value=float(params["hours_per_unit"]), step=0.5)
                new_slots = st.number_input("Equipment Test Slots / Month", min_value=0, value=int(params["equipment_slots"]), step=1)
                new_rig_min = st.number_input("Test Rig Minutes Available / Month", min_value=0.0, value=float(params["test_rig_minutes_available"]), step=40.0)
                new_rig_per = st.number_input("Rig Minutes / Test", min_value=1.0, value=float(params["rig_minutes_per_test"]), step=5.0)

                if st.form_submit_button("Save Resource Parameters"):
                    params["base_price"] = str(d_money(new_p0))
                    params["D0"] = int(new_d0)
                    params["staff_hours"] = float(new_staff)
                    params["hours_per_unit"] = float(new_hpu)
                    params["equipment_slots"] = int(new_slots)
                    params["test_rig_minutes_available"] = float(new_rig_min)
                    params["rig_minutes_per_test"] = float(new_rig_per)
                    c_val, b_str, _ = compute_derived_capacity(params)
                    snap["capacity"] = {"derived_capacity": c_val, "bottleneck": b_str}
                    st.success(f"Parameters updated. Derived monthly capacity: {c_val} tests ({b_str}).")
                    st.rerun()

            st.markdown("#### Required Disruption Test: Calibration Source Replacement")
            st.write(
                "Simulates a calibration source failure that cuts `test_rig_minutes_available` to **800 min** "
                "(capacity drops 20% to **20 tests/month**) and optionally records a **$500 capital equipment outflow**."
            )
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                if st.button("Trigger Disruption (With $500 Capex Approval)"):
                    try:
                        st.session_state.snapshot = apply_calibration_disruption(snap, approve_capex=True)
                        st.warning("Disruption applied: rig minutes = 800 (capacity = 20), $500 capex deducted from cash.")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))
            with dcol2:
                if st.button("Trigger Disruption (Capacity Drop Only, Before Capex)"):
                    st.session_state.snapshot = apply_calibration_disruption(snap, approve_capex=False)
                    st.warning("Disruption applied: rig minutes = 800 (capacity = 20); $500 capex not yet approved.")
                    st.rerun()

        with col_b:
            st.markdown("#### Editable Variable & Fixed Cost Lines")
            with st.form("cost_lines_form"):
                st.markdown("**Variable Cost per Delivered Core Test (USD/unit)**")
                v_edited = {}
                for k, val in snap["cost_lines"]["variable_per_unit"].items():
                    v_edited[k] = st.number_input(f"Variable: {k}", min_value=0.0, value=float(val), step=1.0)

                st.markdown("**Monthly Fixed Operating Costs (USD/month)**")
                f_edited = {}
                for k, val in snap["cost_lines"]["fixed_monthly"].items():
                    f_edited[k] = st.number_input(f"Fixed: {k}", min_value=0.0, value=float(val), step=25.0)

                if st.form_submit_button("Update Cost Lines"):
                    for k, val in v_edited.items():
                        snap["cost_lines"]["variable_per_unit"][k] = str(d_money(val))
                    for k, val in f_edited.items():
                        snap["cost_lines"]["fixed_monthly"][k] = str(d_money(val))
                    st.success("Updated variable and fixed cost lines.")
                    st.rerun()

            st.markdown("#### Capacity Breakdown & Offerings")
            cap_df = pd.DataFrame(
                [
                    {"Constraint": "Engineering Staff Hours", "Formula": f"floor({params['staff_hours']} / {params['hours_per_unit']})", "Max Tests/Mo": cap_breakdown["staff_capacity"]},
                    {"Constraint": "Equipment Test Slots", "Formula": f"{params['equipment_slots']} slots", "Max Tests/Mo": cap_breakdown["equipment_slot_capacity"]},
                    {"Constraint": "Calibration Test Rig Minutes", "Formula": f"floor({params['test_rig_minutes_available']} / {params['rig_minutes_per_test']})", "Max Tests/Mo": cap_breakdown["test_rig_capacity"]},
                ]
            )
            st.dataframe(cap_df, use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------------
    # TAB 3: AP Calculus Math Skills & Challenge Level Panel
    # -----------------------------------------------------------------------
    with tabs[2]:
        level = snap["selected_level"]
        st.subheader(f"AP Calculus Math Skills Panel - {level} Mode")

        # Transfer Check Prompt (Required before moving sliders)
        with st.expander("Transfer Check (Predict Before Moving the Slider)", expanded=True):
            st.write(
                "**Before adjusting the test price slider below, predict:** "
                "If you lower price from **$116.67** to **$110.00**, demand rises from 25 to 27 tests, "
                "but your lab capacity is capped at **25 tests**. Will monthly profit go up or down, and why?"
            )
            st.text_input("Your prediction & reasoning (save in your notes/decision memo):", key="transfer_prediction")

        p_slider = st.slider(
            "Explore Candidate Test Price p (USD/test)",
            min_value=0.0,
            max_value=float(calc_info["p_max"]),
            value=min(float(calc_info["best_constrained_p"]), float(calc_info["p_max"])),
            step=1.0,
        )

        a_val, b_val = calc_info["a"], calc_info["b"]
        v_val, F_val = float(var_unit), float(fixed_mo)
        q_at_p = max(0.0, a_val - b_val * p_slider)
        s_at_p = min(float(cap_now), q_at_p)
        prof_at_p = (p_slider - v_val) * s_at_p - F_val
        whole_s_at_p = math.floor(s_at_p)
        whole_prof_at_p = (p_slider - v_val) * whole_s_at_p - F_val

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Demand q(p)", f"{q_at_p:.2f} tests", f"Cap: {cap_now} tests")
        k2.metric("Realized Sales s(p)", f"{s_at_p:.2f} continuous", f"{whole_s_at_p} whole units")
        k3.metric("Continuous Profit P(p)", fmt_usd(prof_at_p), f"Whole-unit: {fmt_usd(whole_prof_at_p)}")
        k4.metric(
            "Constrained Optimum",
            fmt_usd(calc_info["best_constrained_p"]),
            f"Max Profit: {fmt_usd(calc_info['best_constrained_profit'])}",
        )

        p_grid = np.linspace(0, calc_info["p_max"], 400)
        q_grid = np.maximum(0.0, a_val - b_val * p_grid)
        s_grid = np.minimum(float(cap_now), q_grid)
        p_unconst_grid = (p_grid - v_val) * q_grid - F_val
        p_const_grid = (p_grid - v_val) * s_grid - F_val

        # Mode-specific mathematical outputs & charts
        if level == "Foundation":
            st.markdown(
                f"### Foundation Task: Unconstrained Profit Derivative & Critical Point\n"
                f"- **Profit Function:** $P(p) = (p - {v_val:.0f})({a_val:.0f} - {b_val:.2f}p) - {F_val:.0f}$ on $0 \\le p \\le {calc_info['p_max']:.0f}$\n"
                f"- **First Derivative:** $P'(p) = {a_val + b_val * v_val:.2f} - {2 * b_val:.2f}p$ (units: **USD of profit per USD of price**)\n"
                f"- **Critical Point ($P'(p)=0$):** $p^* = \\${calc_info['p_unconstrained']:.2f}$ -> Unconstrained $q = {calc_info['q_unconstrained']:.2f}$ tests, Unconstrained $P = {fmt_usd(calc_info['profit_unconstrained'])}$\n"
                f"- **Boundary Endpoints:** $P(0) = {fmt_usd(-v_val * a_val - F_val)}$, $P({calc_info['p_max']:.0f}) = {fmt_usd(-F_val)}$"
            )
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(p_grid, p_unconst_grid, label="Unconstrained Profit P(p)", color="#1f77b4", linewidth=2)
            ax.axhline(0, color="black", linestyle="--", linewidth=1, label="Zero Profit Line ($0)")
            ax.scatter([calc_info["p_unconstrained"]], [calc_info["profit_unconstrained"]], color="#d62728", zorder=5, label=f"Critical Point (${calc_info['p_unconstrained']:.2f})")
            ax.axvline(p_slider, color="#2ca02c", linestyle=":", label=f"Selected Price (${p_slider:.2f})")
            ax.set_title(f"NUC-3 Unconstrained Profit Model | {snap['snapshot_id']} | Units: USD")
            ax.set_xlabel("Price per Core Test p (USD/test)")
            ax.set_ylabel("Monthly Profit P(p) (USD/month)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            st.download_button("⬇️ Download Foundation Graph (PNG)", data=fig_to_png_bytes(fig), file_name="NUC3_Foundation_Profit.png", mime="image/png")

        elif level == "Applied":
            p_corn = calc_info["p_corner"]
            st.markdown(
                f"### Applied Task: Piecewise Capacity-Constrained Profit & Derivative\n"
                f"- **Constrained Sales:** $s(p) = \\min({cap_now}, \\max(0, {a_val:.0f} - {b_val:.2f}p))$\n"
                f"- **Capacity Corner:** $q(p) = {cap_now} \\implies p_{{\\text{{corner}}}} = \\frac{{{a_val:.0f} - {cap_now}}}{{{b_val:.2f}}} = \\${p_corn:.2f}$\n"
                f"- **Piecewise Derivative $P'(p)$:**\n"
                f"  - For $0 \\le p < \\${p_corn:.2f}$ (capacity-capped): $P'(p) = +{cap_now}$ USD/dollar\n"
                f"  - At $p = \\${p_corn:.2f}$ (corner): **$P'(p)$ is undefined** (left slope $= +{cap_now}$, right slope $= {a_val + b_val*v_val - 2*b_val*p_corn:.2f}$)\n"
                f"  - For $\\${p_corn:.2f} < p \\le {calc_info['p_max']:.0f}$ (demand-limited): $P'(p) = {a_val + b_val*v_val:.2f} - {2*b_val:.2f}p$\n"
                f"- **Conclusion:** Unconstrained critical point $p = \\${calc_info['p_unconstrained']:.2f}$ requires {calc_info['q_unconstrained']:.1f} tests (> {cap_now} capacity), so the feasible continuous optimum is the corner **$p = \\${calc_info['best_constrained_p']:.2f}$** yielding **{fmt_usd(calc_info['best_constrained_profit'])}**."
            )

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
            ax1.plot(p_grid, p_unconst_grid, linestyle="--", color="#7f7f7f", label="Unconstrained P(p) (ignores capacity)")
            ax1.plot(p_grid, p_const_grid, color="#1f77b4", linewidth=2.2, label=f"Constrained P(p) (cap = {cap_now})")
            ax1.axhline(0, color="black", linestyle=":", linewidth=1)
            ax1.scatter([calc_info["best_constrained_p"]], [calc_info["best_constrained_profit"]], color="#d62728", zorder=5, label=f"Constrained Optimum (${calc_info['best_constrained_p']:.2f})")
            ax1.set_ylabel("Profit (USD/mo)")
            ax1.set_title(f"NUC-3 Piecewise Constrained Profit & Derivative | {snap['snapshot_id']}")
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Piecewise derivative plot with hollow marker at corner
            p_left = np.linspace(0, min(p_corn - 0.1, calc_info["p_max"]), 150)
            p_right = np.linspace(max(p_corn + 0.1, 0), calc_info["p_max"], 200)
            ax2.plot(p_left, np.full_like(p_left, float(cap_now)), color="#ff7f0e", linewidth=2, label="Left branch P'(p) = capacity")
            ax2.plot(p_right, (a_val + b_val * v_val) - 2 * b_val * p_right, color="#2ca02c", linewidth=2, label="Right branch P'(p) = a + bv - 2bp")
            if 0 <= p_corn <= calc_info["p_max"]:
                ax2.scatter([p_corn, p_corn], [float(cap_now), (a_val + b_val * v_val) - 2 * b_val * p_corn], facecolors="white", edgecolors="#d62728", s=60, zorder=6, label="Undefined corner derivative")
            ax2.axhline(0, color="black", linestyle=":", linewidth=1)
            ax2.set_xlabel("Price per Core Test p (USD/test)")
            ax2.set_ylabel("P'(p) (USD / $ price)")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig)
            st.download_button("⬇️ Download Applied Piecewise Graph (PNG)", data=fig_to_png_bytes(fig), file_name="NUC3_Applied_Piecewise.png", mime="image/png")

        else:  # Advanced
            st.markdown(
                f"### Advanced Task: Rate Accumulation Integral & Parameter Sensitivity\n"
                f"1. **Isolated 10-Day Campaign Rate Accumulation ($0 \\le t \\le 10$ days):**\n"
                f"   - Marginal revenue rate: $r(t) = 100 + 20t$ ($/day) $\\implies \\int_0^{{10}} r(t)\\,dt = {fmt_usd(calc_info['accum_rev'])}$\n"
                f"   - Marginal cost rate: $c(t) = 60 + 5t$ ($/day) $\\implies \\int_0^{{10}} c(t)\\,dt = {fmt_usd(calc_info['accum_cost'])}$\n"
                f"   - **Net Accumulated Profit:** $\\int_0^{{10}} (r(t) - c(t))\\,dt = {fmt_usd(calc_info['accum_profit'])}$ *(isolated campaign exercise; does not overwrite monthly ledger)*.\n"
                f"2. **Constrained Optimum & Sensitivity:** At current capacity **{cap_now}**, constrained optimum price is **${calc_info['best_constrained_p']:.2f}** (profit **{fmt_usd(calc_info['best_constrained_profit'])}**)."
            )

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                t_grid = np.linspace(0, 10, 200)
                r_grid = 100.0 + 20.0 * t_grid
                c_grid = 60.0 + 5.0 * t_grid
                fig_int, ax_int = plt.subplots(figsize=(6, 4))
                ax_int.plot(t_grid, r_grid, label="r(t) = 100 + 20t ($/day)", color="#1f77b4", linewidth=2)
                ax_int.plot(t_grid, c_grid, label="c(t) = 60 + 5t ($/day)", color="#d62728", linewidth=2)
                ax_int.fill_between(t_grid, c_grid, r_grid, color="#2ca02c", alpha=0.22, label="Net Profit Integral = $1,150")
                ax_int.set_title(f"Accumulated Net Profit Integral (0<=t<=10) | {snap['snapshot_id']}")
                ax_int.set_xlabel("Campaign Day t (days)")
                ax_int.set_ylabel("Rate (USD/day)")
                ax_int.set_ylim(bottom=0)
                ax_int.legend()
                ax_int.grid(True, alpha=0.3)
                st.pyplot(fig_int)
                st.download_button("⬇️ Download Integral Graph (PNG)", data=fig_to_png_bytes(fig_int), file_name="NUC3_Advanced_Integral.png", mime="image/png")

            with col_g2:
                sens_rows = []
                for c_test in [15, 20, 25, 30]:
                    res_s = compute_calculus_models(int(params["D0"]), float(params["base_price"]), v_val, F_val, c_test)
                    sens_rows.append(
                        {
                            "Capacity (tests/mo)": c_test,
                            "Optimum Price ($)": round(res_s["best_constrained_p"], 2),
                            "Continuous Profit ($)": round(res_s["best_constrained_profit"], 2),
                            "Whole-Unit Profit ($)": round(res_s["whole_unit_profit_at_best"], 2),
                        }
                    )
                st.markdown("**Capacity Sensitivity Table (Holding Demand & Costs Fixed)**")
                st.dataframe(pd.DataFrame(sens_rows), use_container_width=True, hide_index=True)

        # Linked Price-Volume-Profit Table (visible across all levels)
        st.markdown("#### Linked Price-Volume-Profit Table (Continuous vs. Whole-Unit Ledger View)")
        sample_prices = sorted(list({60.0, 80.0, 100.0, 110.0, round(calc_info["best_constrained_p"], 2), 140.0, 160.0, round(p_slider, 2)}))
        table_rows = []
        for sp in sample_prices:
            if 0 <= sp <= calc_info["p_max"]:
                q_c = max(0.0, a_val - b_val * sp)
                s_c = min(float(cap_now), q_c)
                prof_c = (sp - v_val) * s_c - F_val
                s_int = math.floor(s_c)
                prof_int = (sp - v_val) * s_int - F_val
                table_rows.append(
                    {
                        "Price p ($)": f"${sp:,.2f}",
                        "Demand q(p)": f"{q_c:.2f}",
                        "Continuous Sales s(p)": f"{s_c:.2f}",
                        "Continuous Profit ($)": fmt_usd(prof_c),
                        "Whole-Unit Sales": s_int,
                        "Whole-Unit Profit ($)": fmt_usd(prof_int),
                    }
                )
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------------
    # TAB 4: Fixture Replay & Acceptance Tests
    # -----------------------------------------------------------------------
    with tabs[3]:
        st.subheader("Sample Fixture Replay (`sample_data/monthly_fixture.csv`)")
        st.warning(
            "**Fixture-Test Mode Warning:** Replaying `monthly_fixture.csv` resets the simulation to the opening "
            "post-startup state ($4,500 cash) and uses explicit `capacity_override` values strictly to verify ledger math. "
            "Never mix fixture mode with normal mode in the same run."
        )

        fixture_df = load_fixture_df()
        st.dataframe(fixture_df, use_container_width=True, hide_index=True)

        if st.button("▶️ Reset to Opening State & Replay 3-Month Fixture"):
            fresh_snap = build_initial_snapshot(
                team_id=snap["team_id"],
                selected_level=snap["selected_level"],
            )
            replay_summaries = []
            for idx, row in fixture_df.iterrows():
                m_str = str(row["month"])
                fresh_snap, s_row = run_simulation_period(
                    fresh_snap,
                    period_label=m_str,
                    requested_units=int(row["requested"]),
                    ad_cost=d_money(row["ad_cost"]),
                    run_id=f"FIXTURE-{m_str}",
                    capacity_override=int(row["capacity_override"]),
                    mode="fixture",
                )
                replay_summaries.append(
                    {
                        "Month": s_row["period"],
                        "Sold": s_row["sold"],
                        "Revenue": fmt_usd(s_row["revenue"]),
                        "Total Expense": fmt_usd(s_row["total_expense"]),
                        "Profit": fmt_usd(s_row["profit"]),
                        "Closing Cash": fmt_usd(s_row["closing_cash"]),
                    }
                )
            st.session_state.snapshot = fresh_snap
            st.session_state.fixture_results = replay_summaries
            st.success("Fixture replay completed! Compare the results below against the NUC-3 expected values.")
            st.rerun()

        if st.session_state.fixture_results:
            st.markdown("#### Replay Output vs. Expected NUC-3 Fixture Results")
            st.dataframe(pd.DataFrame(st.session_state.fixture_results), use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------------
    # TAB 5: Stage 2-4 Honest Feature Status
    # -----------------------------------------------------------------------
    with tabs[4]:
        st.subheader("Implementation Status & Roadmap")
        status_df = pd.DataFrame(
            [
                {"Stage": "Stage 1", "Modules": "Startup Financing, Editable Inputs, Capacity Engine, Dated Ledger, JSON Save/Restore, AP Calculus Panel, Fixture Tests", "Status": "IMPLEMENTED"},
                {"Stage": "Stage 2", "Modules": "Full Report Center (Income Statement, Cash Flow, Variance, Balance Sheet), Costed Marketing Studio, AI Recommendations Handoff", "Status": "NOT IMPLEMENTED (Planned Stage 2)"},
                {"Stage": "Stage 3", "Modules": "Frozen-Snapshot Practice Assessment Panel & Cross-Course Evidence Artifacts", "Status": "NOT IMPLEMENTED (Planned Stage 3)"},
                {"Stage": "Stage 4", "Modules": "Optional Demonstration Storefront (lowest priority, after core tests pass)", "Status": "NOT IMPLEMENTED (Optional Stage 4)"},
            ]
        )
        st.dataframe(status_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
