import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.analysis import Insight, Alert, AuditEvent
from app.schemas.analysis import InsightRead, AlertRead, AlertUpdateRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1", tags=["Insights & Alerts"])

@router.get("/insights", response_model=List[InsightRead])
def list_insights(
    insight_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Insight).filter(Insight.user_id == current_user.user_id)
    if insight_type:
        query = query.filter(Insight.insight_type == insight_type)
    if severity:
        query = query.filter(Insight.severity == severity)
    
    return query.order_by(Insight.created_at.desc()).all()

@router.get("/insights/{insight_id}", response_model=InsightRead)
def get_insight_detail(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ins = db.query(Insight).filter(
        Insight.insight_id == insight_id,
        Insight.user_id == current_user.user_id
    ).first()
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found.")
    return ins

@router.get("/alerts", response_model=List[AlertRead])
def list_alerts(
    status_filter: Optional[str] = Query(None), # UNREAD, ACKNOWLEDGED, RESOLVED
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Alert).filter(Alert.user_id == current_user.user_id)
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    return query.order_by(Alert.created_at.desc()).all()

@router.patch("/alerts/{alert_id}", response_model=AlertRead)
def update_alert(
    alert_id: str,
    req: AlertUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.alert_id == alert_id,
        Alert.user_id == current_user.user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    if req.status not in ["ACKNOWLEDGED", "RESOLVED", "UNREAD"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be ACKNOWLEDGED, RESOLVED, or UNREAD.")

    old_status = alert.status
    alert.status = req.status
    if req.resolution_notes:
        alert.resolution_notes = req.resolution_notes
    alert.updated_at = datetime.datetime.utcnow()

    # Record audit event
    audit = AuditEvent(
        event_id=f"aud_{datetime.datetime.utcnow().timestamp()}",
        user_id=current_user.user_id,
        actor="user",
        action="ALERT_STATUS_UPDATE",
        entity_type="Alert",
        entity_id=alert_id,
        details={"old_status": old_status, "new_status": req.status, "notes": req.resolution_notes}
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    return alert
