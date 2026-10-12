import uuid
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.analysis import Alert, AuditEvent

class NotificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("NotificationAgent")

    def run(self, db: Session, user_id: str, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        created_count = 0
        updated_count = 0

        for ins in insights:
            ins_id = ins.get("insight_id")
            ins_type = ins.get("type", "GENERAL")
            sev = ins.get("severity", "MEDIUM")
            obs = ins.get("observation", "")
            action = ins.get("action", "")

            # Deduplication key: user_id + ":" + insight_type + ":" + entity_key + ":" + period
            entity_key = ins.get("evidence", {}).get("category") or ins.get("evidence", {}).get("merchant") or "global"
            period = ins.get("evidence", {}).get("period") or datetime.date.today().strftime("%Y-%m")
            dedup_key = f"{user_id}:{ins_type}:{entity_key}:{period}"

            existing_alert = db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.deduplication_key == dedup_key
            ).first()

            if existing_alert:
                # Update severity and message instead of duplicating
                if existing_alert.severity != sev or existing_alert.message != obs:
                    existing_alert.severity = sev
                    existing_alert.message = obs
                    existing_alert.updated_at = datetime.datetime.utcnow()
                    updated_count += 1
            else:
                alert_id = f"alt_{uuid.uuid4().hex[:8]}"
                new_alert = Alert(
                    alert_id=alert_id,
                    user_id=user_id,
                    deduplication_key=dedup_key,
                    insight_id=ins_id,
                    title=f"Alert: {ins_type.replace('_', ' ').title()}",
                    message=obs,
                    severity=sev,
                    status="UNREAD"
                )
                db.add(new_alert)
                created_count += 1

                # Record audit event
                audit = AuditEvent(
                    event_id=f"aud_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    actor="system.notification_agent",
                    action="ALERT_PUBLISHED",
                    entity_type="Alert",
                    entity_id=alert_id,
                    details={"deduplication_key": dedup_key, "severity": sev}
                )
                db.add(audit)

        db.commit()

        return {
            "alerts_created": created_count,
            "alerts_updated": updated_count
        }

notification_agent = NotificationAgent()
