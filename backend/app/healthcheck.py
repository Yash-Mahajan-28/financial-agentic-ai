import sys
import requests
from app.config import settings
from app.database import SessionLocal
from sqlalchemy import text

def check_api():
    try:
        url = f"http://127.0.0.1:{settings.API_PORT}/health/live"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            sys.exit(0)
    except Exception:
        pass
    sys.exit(1)

def check_worker():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        sys.exit(0)
    except Exception:
        sys.exit(1)
    finally:
        db.close()

def check_scheduler():
    sys.exit(0)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "api"
    if target == "api":
        check_api()
    elif target == "worker":
        check_worker()
    elif target == "scheduler":
        check_scheduler()
    else:
        sys.exit(0)
