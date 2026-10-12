import uuid
import time
import datetime
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun
from app.models.user import User
from app.agents import (
    spending_agent,
    budget_agent,
    health_agent,
    anomaly_agent,
    recurring_agent,
    forecast_agent,
    advisor_agent,
    notification_agent
)
from app.rules.rules_engine import rules_engine

logger = logging.getLogger(__name__)

class MasterOrchestrator:
    def __init__(self):
        self._active_runs = {} # Track active runs to coalesce duplicates

    def run_full_pipeline(self, db: Session, user_id: str, trigger_reason: str = "MANUAL") -> Dict[str, Any]:
        start_time = time.time()
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        data_version = f"v_{int(time.time())}"
        cutoff_date = datetime.date.today().strftime("%Y-%m-%d")

        logger.info(f"Master Orchestrator initiated run [{run_id}] for user [{user_id}] due to [{trigger_reason}].")
        stages_executed = []

        # Create AnalysisRun upfront to satisfy foreign key constraints on child tables (e.g. insights.run_id)
        run_record = AnalysisRun(
            run_id=run_id,
            user_id=user_id,
            data_version=data_version,
            config_version=rules_engine.version,
            cutoff_date=cutoff_date,
            status="RUNNING",
            summary_metrics={},
            wellness_score={}
        )
        db.add(run_record)
        db.commit()

        try:
            # Stage 1: Spending Analysis Agent
            stages_executed.append("SPENDING_ANALYSIS")
            spending_res = spending_agent.execute(db, user_id)
            latest_month = spending_res["latest_month"]
            latest_month_summary = spending_res["latest_month_summary"]
            category_spending = {k: v["current_spending"] for k, v in latest_month_summary["categories"].items()}
            net_income = latest_month_summary["total_income"]
            net_spending = latest_month_summary["total_spending"]
            surplus = latest_month_summary["surplus"]

            # Stage 2: Budget Planning Agent
            stages_executed.append("BUDGET_PLANNING")
            budget_res = budget_agent.execute(db, user_id, latest_month, category_spending, net_income)

            # Stage 3: Anomaly Detection Agent (MAD & Duplicates)
            stages_executed.append("ANOMALY_DETECTION")
            anomaly_res = anomaly_agent.execute(db, user_id)

            # Stage 4: Subscription Intelligence Agent
            stages_executed.append("SUBSCRIPTION_INTELLIGENCE")
            recurring_res = recurring_agent.execute(db, user_id)

            # Stage 5: Health Scoring Agent
            stages_executed.append("HEALTH_SCORING")
            # Essential spending: Housing + Groceries + Utilities + Transport
            essential_spend = (
                category_spending.get("Housing & Rent", Decimal("0.00")) +
                category_spending.get("Groceries", Decimal("0.00")) +
                category_spending.get("Utilities", Decimal("0.00")) +
                category_spending.get("Transportation", Decimal("0.00"))
            )
            health_res = health_agent.execute(
                db,
                user_id,
                net_monthly_surplus=surplus,
                total_overspend=budget_res["total_overspend"],
                total_budget_limit=budget_res["total_budget_limit"],
                essential_monthly_spending=essential_spend
            )

            # Stage 6: Cash Flow Forecast Agent
            stages_executed.append("CASH_FLOW_FORECAST")
            forecast_res = forecast_agent.execute(db, user_id)

            # Stage 7: Financial Advisor Agent (Prioritizes & generates insight templates)
            stages_executed.append("FINANCIAL_ADVISOR")
            advisor_res = advisor_agent.execute(
                db,
                user_id,
                run_id=run_id,
                budget_results=budget_res,
                forecast_results=forecast_res,
                anomaly_results=anomaly_res,
                recurring_results=recurring_res
            )

            # Stage 8: Notification Agent (Deduplicated alerts)
            stages_executed.append("NOTIFICATIONS")
            notification_res = notification_agent.execute(
                db,
                user_id,
                insights=advisor_res["insights"]
            )

            # Stage 9: Atomic Snapshot Publication
            stages_executed.append("SNAPSHOT_PUBLICATION")
            run_record = db.query(AnalysisRun).filter(AnalysisRun.run_id == run_id).first()
            if run_record:
                run_record.status = "COMPLETED"
                run_record.summary_metrics = {
                    "period": latest_month,
                    "net_income": str(net_income),
                    "net_spending": str(net_spending),
                    "monthly_surplus": str(surplus),
                    "total_budget_limit": str(budget_res["total_budget_limit"]),
                    "overall_budget_utilization_pct": str(budget_res["overall_utilization_pct"])
                }
                run_record.wellness_score = {
                    "score": health_res.get("score"),
                    "status": health_res.get("status"),
                    "savings_discipline": str(health_res.get("savings_discipline")) if health_res.get("savings_discipline") is not None else None,
                    "budget_discipline": str(health_res.get("budget_discipline")) if health_res.get("budget_discipline") is not None else None,
                    "debt_burden": str(health_res.get("debt_burden")) if health_res.get("debt_burden") is not None else None,
                    "reserve_coverage": str(health_res.get("reserve_coverage")) if health_res.get("reserve_coverage") is not None else None,
                    "formula_version": health_res.get("formula_version")
                }
                db.commit()

            total_duration_ms = (time.time() - start_time) * 1000.0
            logger.info(f"Master Orchestrator completed run [{run_id}] in {total_duration_ms:.2f}ms.")

            return {
                "run_id": run_id,
                "data_version": data_version,
                "status": "COMPLETED",
                "stages_executed": stages_executed,
                "total_duration_ms": total_duration_ms,
                "spending_summary": latest_month_summary,
                "budget_summary": budget_res,
                "wellness_score": health_res,
                "forecast_summary": forecast_res,
                "insights": advisor_res["insights"],
                "alerts_summary": notification_res
            }

        except Exception as e:
            logger.error(f"Master Orchestrator run [{run_id}] failed: {e}", exc_info=True)
            db.rollback()
            raise e

orchestrator = MasterOrchestrator()
