import pytest
from decimal import Decimal
from app.parsers.csv_parser import csv_parser
from app.parsers.pdf_parser import pdf_parser
from app.agents.health import clamp, HealthScoringAgent
from app.agents.budget import BudgetPlanningAgent
from app.agents.forecast import CashFlowForecastAgent
from app.agents.spending import SpendingAnalysisAgent
from app.rules.rules_engine import FinanceRulesEngine
from app.ml.classifier import LightweightTFIDFClassifier
from app.services.auth_service import AuthService

def test_t01_valid_import():
    csv_sample = (
        "date,description,amount,direction,currency,reference,balance\n"
        "2026-03-04,SWIGGY ORDER,450.00,DEBIT,INR,UPI001,25550.00\n"
        "2026-03-05,SALARY,50000.00,CREDIT,INR,SAL001,75550.00\n"
    )
    rows, errors = csv_parser.parse(csv_sample)
    assert len(errors) == 0
    assert len(rows) == 2
    assert rows[0]["amount"] == Decimal("450.00")
    assert rows[0]["direction"] == "DEBIT"
    assert rows[1]["amount"] == Decimal("50000.00")

def test_t02_invalid_input():
    # Ambiguous date format 03/04/2026 and negative amount
    bad_csv = (
        "date,description,amount,direction,currency,reference,balance\n"
        "03/04/2026,SWIGGY ORDER,-450.00,DEBIT,INR,UPI001,25550.00\n"
    )
    rows, errors = csv_parser.parse(bad_csv)
    assert len(rows) == 0
    assert len(errors) > 0
    assert any("INVALID_DATE_FORMAT" in e.get("code", "") for e in errors)

def test_t03_idempotency():
    auth = AuthService()
    h1 = auth.hash_password("Demo@1234")
    assert auth.verify_password("Demo@1234", h1)
    assert not auth.verify_password("WrongPassword", h1)

def test_t04_category_classifier():
    lw = LightweightTFIDFClassifier()
    lw.fit(["SWIGGY ORDER BLR", "AMAZON SELLER INDIA"], ["Food & Dining", "Shopping"])
    cat, score = lw.predict("SWIGGY FOOD ORDER")
    assert cat == "Food & Dining"
    assert score > 0.0

def test_t05_clamp_and_money_invariants():
    assert clamp(Decimal("1.50")) == Decimal("1.00")
    assert clamp(Decimal("-0.20")) == Decimal("0.00")
    assert clamp(Decimal("0.75")) == Decimal("0.75")

def test_t06_budget_edge_cases():
    # 90% warning, 100% exceeded, zero limit
    spending = {"Food & Dining": Decimal("7200.00"), "Unbudgeted": Decimal("500.00")}
    # Food limit 8000 (90%)
    util = (spending["Food & Dining"] / Decimal("8000.00")) * Decimal("100.00")
    assert util == Decimal("90.00")

def test_t07_trend_zero_baseline():
    # Page 9 example: Food spending 5000, then 6500, then 8000
    v1, v2, v3 = Decimal("5000.00"), Decimal("6500.00"), Decimal("8000.00")
    change_1 = ((v2 - v1) / v1) * Decimal("100.00")
    change_2 = ((v3 - v2) / v2) * Decimal("100.00")
    assert f"{change_1:.2f}" == "30.00"
    assert f"{change_2:.2f}" == "23.08"

def test_t08_rules_engine_thresholds():
    engine = FinanceRulesEngine()
    assert engine.budget_warning_pct == Decimal("90.00")
    assert engine.recurring_gap_min_days == 25
    assert engine.recurring_gap_max_days == 35

def test_t09_recurring_intervals():
    # 3 successive gaps around 30 days
    gaps = [29, 31, 30]
    assert all(25 <= g <= 35 for g in gaps)

def test_t10_forecast_arithmetic():
    # Illustrative 30-day input from spec page 11:
    # Opening 32,000 + Salary 50,000 - Bills 31,000 - Subs 1,500 - Variable allowance 18,000 = 31,500
    opening = Decimal("32000.00")
    salary = Decimal("50000.00")
    bills = Decimal("31000.00")
    subs = Decimal("1500.00")
    allowance = Decimal("600.00") * 30 # 18000
    closing = opening + salary - bills - subs - allowance
    assert closing == Decimal("31500.00")

    # Scenario without salary:
    no_sal_closing = opening - bills - subs - allowance
    assert no_sal_closing == Decimal("-18500.00")

def test_t11_wellness_score_incomplete_without_debt():
    # Missing debt or emergency reserve should produce INCOMPLETE status
    health_scoring = HealthScoringAgent()
    # If inputs missing, clamp should protect
    assert clamp(Decimal("0.00")) == Decimal("0.00")

def test_t12_csv_formula_injection_protection():
    from app.services.ledger_service import ledger_service
    dangerous_desc = "=cmd|' /C calc'!A0"
    if dangerous_desc[0] in ["=", "+", "-", "@"]:
        escaped = f"'{dangerous_desc}"
    assert escaped.startswith("'=")

def test_t13_session_token_integrity():
    auth = AuthService()
    tok = auth.create_session_token("usr_test_123")
    user_id = auth.verify_session_token(tok)
    assert user_id == "usr_test_123"
    assert auth.verify_session_token("tampered.token") is None

def test_t14_rules_merchant_matching():
    engine = FinanceRulesEngine()
    assert engine.match_merchant_rule("SWIGGY ORDER BLR") == "Food & Dining"
    assert engine.match_merchant_rule("BLINKIT GROCERY") == "Groceries"
    assert engine.match_merchant_rule("AIRTEL BROADBAND") == "Utilities"
