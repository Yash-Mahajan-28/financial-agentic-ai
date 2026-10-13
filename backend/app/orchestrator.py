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

from app.agents.multi_agent_graph import financial_multi_agent_graph

logger = logging.getLogger(__name__)

class MasterOrchestrator:
    def __init__(self):
        self._active_runs = {}

    def run_full_pipeline(self, db: Session, user_id: str, trigger_reason: str = "MANUAL") -> Dict[str, Any]:
        start_time = time.time()
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        data_version = f"v_{int(time.time())}"
        cutoff_date = datetime.date.today().strftime("%Y-%m-%d")

        logger.info(f"LangGraph Orchestrator initiating multi-agent run [{run_id}] for user [{user_id}] via [{trigger_reason}].")

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
            initial_state = {
                "run_id": run_id,
                "user_id": user_id,
                "data_version": data_version,
                "trigger_reason": trigger_reason,
                "current_phase": "INITIATED",
                "execution_plan": [],
                "stages_completed": [],
                "spending_artifacts": {},
                "budget_artifacts": {},
                "anomaly_artifacts": {},
                "recurring_artifacts": {},
                "forecast_artifacts": {},
                "wellness_artifacts": {},
                "draft_insights": [],
                "reviewer_verdict": "PENDING",
                "reviewer_feedback": [],
                "iteration_count": 0,
                "max_iterations": 2,
                "final_insights": [],
                "execution_trace": [],
                "status": "RUNNING",
                "error": None
            }

            # Invoke LangGraph Multi-Agent StateGraph
            final_state = financial_multi_agent_graph.invoke(initial_state)

            total_duration_ms = (time.time() - start_time) * 1000.0
            logger.info(f"LangGraph Multi-Agent pipeline completed run [{run_id}] in {total_duration_ms:.2f}ms.")

            return {
                "run_id": run_id,
                "data_version": data_version,
                "status": "COMPLETED",
                "stages_executed": final_state.get("stages_completed", []),
                "execution_plan": final_state.get("execution_plan", []),
                "execution_trace": final_state.get("execution_trace", []),
                "reviewer_verdict": final_state.get("reviewer_verdict", "APPROVED"),
                "total_duration_ms": total_duration_ms,
                "spending_summary": final_state.get("spending_artifacts", {}),
                "budget_summary": final_state.get("budget_artifacts", {}),
                "wellness_score": final_state.get("wellness_artifacts", {}),
                "forecast_summary": final_state.get("forecast_artifacts", {}),
                "insights": final_state.get("final_insights", []),
                "alerts_summary": final_state.get("final_insights", [])
            }

        except Exception as e:
            logger.error(f"LangGraph Multi-Agent run [{run_id}] failed: {e}", exc_info=True)
            db.rollback()
            raise e

orchestrator = MasterOrchestrator()
