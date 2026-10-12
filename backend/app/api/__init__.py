from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router
from app.api.transactions import router as transactions_router
from app.api.budgets import router as budgets_router
from app.api.dashboard import router as dashboard_router
from app.api.insights import router as insights_router
from app.api.forecast import router as forecast_router
from app.api.advisor import router as advisor_router
from app.api.accounts import router as accounts_router
from app.api.system import router as system_router

__all__ = [
    "auth_router",
    "uploads_router",
    "transactions_router",
    "budgets_router",
    "dashboard_router",
    "insights_router",
    "forecast_router",
    "advisor_router",
    "accounts_router",
    "system_router"
]
