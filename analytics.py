"""
Analytics and financial forecasting engine.
Handles runway projection, goal planning, and "what-if" scenario modeling.
"""

from typing import Dict, Any, List, Optional


def calculate_runway(current_balance: float, monthly_burn: float) -> Dict[str, Any]:
    """
    Calculates runway in months.
    If monthly_burn <= 0, the balance is either static or growing (infinite runway).
    """
    if monthly_burn <= 0:
        return {
            "months": float("inf"),
            "is_infinite": True,
            "status": "Surplus / Growing"
        }
    
    months = current_balance / monthly_burn
    return {
        "months": round(months, 1),
        "is_infinite": False,
        "status": f"{round(months, 1)} months"
    }


def calculate_needed_savings(
    current_balance: float,
    target_amount: float,
    target_months: int
) -> Dict[str, Any]:
    """
    Calculates total and monthly savings required to hit a future financial goal.
    """
    total_needed = max(0.0, target_amount - current_balance)
    months = max(1, target_months)
    monthly_needed = total_needed / months
    
    return {
        "total_needed": round(total_needed, 2),
        "target_months": months,
        "monthly_savings_needed": round(monthly_needed, 2),
        "is_already_reached": current_balance >= target_amount
    }


def simulate_scenarios(
    starting_balance: float,
    base_monthly_income: float,
    base_fixed_expense: float,
    base_variable_expense: float,
    income_delta_pct: float = 0.0,
    scenario_monthly_income: Optional[float] = None,
    fixed_delta_eur: float = 0.0,
    variable_delta_pct: float = 0.0,
    months: int = 12
) -> Dict[str, Any]:
    """
    Simulates monthly finances across `months` for both baseline and an adjusted scenario.
    - scenario_monthly_income: exact Euro figure for new monthly salary (takes precedence over income_delta_pct).
    - income_delta_pct: percentage change in income (-50% to +50%).
    - fixed_delta_eur: absolute Euro change in fixed costs (-500€ to +500€).
    - variable_delta_pct: percentage change in variable spending (-100% to +100%).
    """
    # Baseline calculations
    base_net = base_monthly_income - base_fixed_expense - base_variable_expense
    
    # Scenario adjusted calculations: exact income or percentage adjustment
    if scenario_monthly_income is not None:
        target_income = max(0.0, float(scenario_monthly_income))
    else:
        target_income = max(0.0, base_monthly_income * (1 + (income_delta_pct / 100.0)))

    scenario_fixed = max(0.0, base_fixed_expense + fixed_delta_eur)
    scenario_variable = max(0.0, base_variable_expense * (1 + (variable_delta_pct / 100.0)))
    scenario_net = target_income - scenario_fixed - scenario_variable
    
    baseline_timeline: List[Dict[str, Any]] = []
    scenario_timeline: List[Dict[str, Any]] = []
    
    current_base_bal = starting_balance
    current_scen_bal = starting_balance
    
    for m in range(1, months + 1):
        current_base_bal += base_net
        current_scen_bal += scenario_net
        
        baseline_timeline.append({
            "month": m,
            "projected_balance": round(current_base_bal, 2),
            "net_flow": round(base_net, 2)
        })
        scenario_timeline.append({
            "month": m,
            "projected_balance": round(current_scen_bal, 2),
            "net_flow": round(scenario_net, 2)
        })
        
    return {
        "starting_balance": round(starting_balance, 2),
        "baseline_monthly_net": round(base_net, 2),
        "scenario_monthly_income": round(target_income, 2),
        "scenario_monthly_fixed": round(scenario_fixed, 2),
        "scenario_monthly_variable": round(scenario_variable, 2),
        "scenario_monthly_net": round(scenario_net, 2),
        "baseline_timeline": baseline_timeline,
        "scenario_timeline": scenario_timeline,
        "3_month_scenario_balance": scenario_timeline[min(2, months - 1)]["projected_balance"],
        "6_month_scenario_balance": scenario_timeline[min(5, months - 1)]["projected_balance"],
        "12_month_scenario_balance": scenario_timeline[min(11, months - 1)]["projected_balance"]
    }
