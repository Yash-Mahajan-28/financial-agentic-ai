import os
import json
import logging
from decimal import Decimal
from typing import Dict, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

class FinanceRulesEngine:
    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path or settings.RULES_PATH
        self.rules_data: Dict[str, Any] = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading finance rules from {self.rules_path}: {e}")
        
        # Hardened fallback defaults matching specification page 15
        return {
            "version": "finance-v1",
            "currency": "INR",
            "budget": {"warning_pct": "90.00", "exceeded_pct": "100.00"},
            "anomaly": {
                "history_days": 90,
                "minimum_samples": 10,
                "median_multiplier": "3",
                "mad_multiplier": "6",
                "minimum_amount": "2000.00"
            },
            "recurring": {
                "minimum_charges": 3,
                "gap_min_days": 25,
                "gap_max_days": 35,
                "amount_tolerance": "0.10"
            },
            "forecast": {"horizon_days": 30},
            "monitoring": {"schedule_minutes": 60, "stale_after_days": 7},
            "merchant_category_rules": {
                "SWIGGY": "Food & Dining",
                "ZOMATO": "Food & Dining",
                "STARBUCKS": "Food & Dining",
                "BLINKIT": "Groceries",
                "ZEPTO": "Groceries",
                "BIGBASKET": "Groceries",
                "BESCOM": "Utilities",
                "AIRTEL": "Utilities",
                "RENT": "Housing & Rent",
                "UBER": "Transportation",
                "OLA": "Transportation",
                "NETFLIX": "Entertainment",
                "SPOTIFY": "Entertainment",
                "CULT FIT": "Health & Fitness",
                "APOLLO": "Health & Fitness",
                "AMAZON": "Shopping",
                "ZERODHA": "Investments",
                "GROWW": "Investments",
                "SALARY": "Income",
                "LOAN EMI": "Debt Settlement"
            }
        }

    @property
    def version(self) -> str:
        return self.rules_data.get("version", "finance-v1")

    @property
    def currency(self) -> str:
        return self.rules_data.get("currency", "INR")

    @property
    def budget_warning_pct(self) -> Decimal:
        return Decimal(str(self.rules_data.get("budget", {}).get("warning_pct", "90.00")))

    @property
    def budget_exceeded_pct(self) -> Decimal:
        return Decimal(str(self.rules_data.get("budget", {}).get("exceeded_pct", "100.00")))

    @property
    def anomaly_history_days(self) -> int:
        return int(self.rules_data.get("anomaly", {}).get("history_days", 90))

    @property
    def anomaly_min_samples(self) -> int:
        return int(self.rules_data.get("anomaly", {}).get("minimum_samples", 10))

    @property
    def anomaly_median_multiplier(self) -> Decimal:
        return Decimal(str(self.rules_data.get("anomaly", {}).get("median_multiplier", "3")))

    @property
    def anomaly_mad_multiplier(self) -> Decimal:
        return Decimal(str(self.rules_data.get("anomaly", {}).get("mad_multiplier", "6")))

    @property
    def anomaly_min_amount(self) -> Decimal:
        return Decimal(str(self.rules_data.get("anomaly", {}).get("minimum_amount", "2000.00")))

    @property
    def recurring_min_charges(self) -> int:
        return int(self.rules_data.get("recurring", {}).get("minimum_charges", 3))

    @property
    def recurring_gap_min_days(self) -> int:
        return int(self.rules_data.get("recurring", {}).get("gap_min_days", 25))

    @property
    def recurring_gap_max_days(self) -> int:
        return int(self.rules_data.get("recurring", {}).get("gap_max_days", 35))

    @property
    def recurring_amount_tolerance(self) -> Decimal:
        return Decimal(str(self.rules_data.get("recurring", {}).get("amount_tolerance", "0.10")))

    @property
    def forecast_horizon_days(self) -> int:
        return int(self.rules_data.get("forecast", {}).get("horizon_days", 30))

    def match_merchant_rule(self, description: str) -> Optional[str]:
        desc_upper = description.upper()
        merchant_rules = self.rules_data.get("merchant_category_rules", {})
        for keyword, category in merchant_rules.items():
            if keyword.upper() in desc_upper:
                return category
        return None

rules_engine = FinanceRulesEngine()
