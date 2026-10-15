import os
import csv
import json
import uuid
import logging
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models.user import User, Account
from app.models.budget import Budget, Obligation
from app.models.transaction import Transaction, TransactionSource
from app.models.upload import Upload, Job
from app.models.analysis import AnalysisRun
from app.services.auth_service import auth_service
from app.ml.train import train_classifier
from app.orchestrator import orchestrator
from app.config import settings

logger = logging.getLogger(__name__)

def seed_database(db: Session):
    # Check if demo user already exists
    demo_user = db.query(User).filter(User.email == "demo@agentic.finance").first()
    if demo_user:
        completed_run = db.query(AnalysisRun).filter(
            AnalysisRun.user_id == demo_user.user_id,
            AnalysisRun.status == "COMPLETED"
        ).first()
        if completed_run:
            logger.info("Demo user already exists with completed analysis run. Skipping bootstrap seeding.")
            return
        else:
            logger.info("Demo user exists but analysis pipeline is incomplete. Re-running pipeline...")
            orchestrator.run_full_pipeline(db, demo_user.user_id, trigger_reason="BOOTSTRAP_RETRY")
            logger.info("Analysis pipeline completed successfully!")
            return

    logger.info("Bootstrapping database with seed accounts, budgets, and statements...")

    # 1. Ensure ML Model is trained
    train_classifier(settings.MODEL_PATH)

    # 2. Create Demo User
    user_id = "usr_demo_01"
    hashed_pw = auth_service.hash_password(settings.DEMO_PASSWORD)
    user = User(
        user_id=user_id,
        email="demo@agentic.finance",
        hashed_password=hashed_pw,
        full_name="Yash Mahajan",
        currency="INR",
        confirmed_net_income=Decimal("50000.00"),
        confirmed_monthly_debt=Decimal("7000.00"),
        liquid_emergency_reserve=Decimal("75000.00"),
        target_savings_rate=Decimal("0.20"),
        debt_burden_ceiling=Decimal("0.40"),
        reserve_target_months=3
    )
    db.add(user)
    db.commit()

    # 3. Create Seed Accounts
    accounts_data = [
        ("acc_hdfc_01", "HDFC Primary Savings", "CHECKING", "•••• 8492", Decimal("32000.00"), "2026-04-01"),
        ("acc_icici_cc_02", "ICICI Coral Credit Card", "CREDIT_CARD", "•••• 4109", Decimal("-2899.00"), "2026-04-01"),
        ("acc_axis_03", "Axis Secondary Savings", "SAVINGS", "•••• 7721", Decimal("38100.00"), "2026-04-01")
    ]
    for acc_id, name, acc_type, masked, bal, dt in accounts_data:
        if not db.query(Account).filter(Account.account_id == acc_id).first():
            acc = Account(
                account_id=acc_id,
                user_id=user_id,
                account_name=name,
                account_type=acc_type,
                account_number_masked=masked,
                currency="INR",
                balance=bal,
                balance_as_of=dt
            )
            db.add(acc)
    db.commit()

    # 4. Create Budgets for 2026-03
    budgets_map = {
        "Food & Dining": Decimal("8000.00"),
        "Groceries": Decimal("6000.00"),
        "Utilities": Decimal("3500.00"),
        "Housing & Rent": Decimal("18000.00"),
        "Transportation": Decimal("3000.00"),
        "Entertainment": Decimal("1500.00"),
        "Shopping": Decimal("4000.00"),
        "Health & Fitness": Decimal("2500.00")
    }
    for cat, lim in budgets_map.items():
        if not db.query(Budget).filter(Budget.user_id == user_id, Budget.month == "2026-03", Budget.category == cat).first():
            b = Budget(
                budget_id=f"bg_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                month="2026-03",
                category=cat,
                limit_amount=lim
            )
            db.add(b)
    db.commit()

    # 5. Create Scheduled Obligations
    obligations_data = [
        ("ob_sal_01", "TechCorp Monthly Salary", Decimal("50000.00"), "CREDIT", 5, "Income", "SALARY", "acc_hdfc_01"),
        ("ob_rent_02", "Apartment Rent to Landlord", Decimal("18000.00"), "DEBIT", 3, "Housing & Rent", "BILL", "acc_hdfc_01"),
        ("ob_emi_03", "Personal Loan EMI", Decimal("7000.00"), "DEBIT", 10, "Debt Settlement", "EMI", "acc_hdfc_01"),
        ("ob_elec_04", "BESCOM Electricity & Utilities", Decimal("2800.00"), "DEBIT", 12, "Utilities", "BILL", "acc_hdfc_01"),
        ("ob_sub_05", "Digital Subscriptions (Netflix, Spotify, Gym)", Decimal("2268.00"), "DEBIT", 18, "Entertainment", "SUBSCRIPTION", "acc_hdfc_01")
    ]
    for ob_id, title, amt, direction, day, cat, ob_type, a_id in obligations_data:
        if not db.query(Obligation).filter(Obligation.obligation_id == ob_id).first():
            ob = Obligation(
                obligation_id=ob_id,
                user_id=user_id,
                title=title,
                amount=amt,
                direction=direction,
                day_of_month=day,
                category=cat,
                obligation_type=ob_type,
                account_id=a_id,
                is_confirmed=True,
                is_active=True
            )
            db.add(ob)
    db.commit()

    def find_fixture(filename: str):
        candidates = [
            os.path.join("data", "fixtures", filename),
            os.path.join("backend", "data", "fixtures", filename),
            os.path.join("dataset", "statements", filename),
            os.path.join("..", "dataset", "statements", filename),
            os.path.join("/app", "data", "fixtures", filename),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    from app.parsers.csv_parser import csv_parser
    from app.agents import categorization_agent

    # 6. Seed HDFC Statement Fixtures
    fixture_path = find_fixture("hdfc_bank_savings.csv")
    upload_id_hdfc = "up_fixture_hdfc_01"
    if fixture_path and not db.query(Upload).filter(Upload.upload_id == upload_id_hdfc).first():
        upload = Upload(
            upload_id=upload_id_hdfc,
            user_id=user_id,
            account_id="acc_hdfc_01",
            content_hash="hash_fixture_hdfc_01",
            storage_key=fixture_path,
            original_filename="hdfc_bank_savings.csv",
            parser_version="v1.0",
            period="2026-01 to 2026-03"
        )
        db.add(upload)
        db.commit()

        with open(fixture_path, "r", encoding="utf-8") as f:
            content_str = f.read()
        parsed_rows, _ = csv_parser.parse(content_str)
        cat_res = categorization_agent.execute(db, user_id, parsed_rows)

        for r in cat_res["categorized_transactions"]:
            tx_id = f"tx_{uuid.uuid4().hex[:10]}"
            t_rec = Transaction(
                transaction_id=tx_id,
                user_id=user_id,
                account_id="acc_hdfc_01",
                date=r["date"],
                description=r["description"],
                amount=r["amount"],
                direction=r["direction"],
                currency=r["currency"],
                transaction_type=r["transaction_type"],
                category=r["category"],
                category_source=r["category_source"],
                classifier_score=r["classifier_score"],
                reference=r["reference"],
                review_state=r["review_state"],
                is_duplicate_candidate=(r["reference"] == "UPI1048")
            )
            db.add(t_rec)

            s_rec = TransactionSource(
                transaction_id=tx_id,
                upload_id=upload_id_hdfc,
                row_number=r.get("row_number"),
                page_number=r.get("page_number"),
                raw_text=r.get("raw_text", ""),
                parse_status="SUCCESS"
            )
            db.add(s_rec)
        db.commit()

    # 7. Seed ICICI CC Statement Fixtures
    cc_fixture = find_fixture("icici_credit_card.csv")
    upload_id_icici = "up_fixture_icici_02"
    if cc_fixture and not db.query(Upload).filter(Upload.upload_id == upload_id_icici).first():
        upload = Upload(
            upload_id=upload_id_icici,
            user_id=user_id,
            account_id="acc_icici_cc_02",
            content_hash="hash_fixture_icici_02",
            storage_key=cc_fixture,
            original_filename="icici_credit_card.csv",
            parser_version="v1.0",
            period="2026-01 to 2026-03"
        )
        db.add(upload)
        db.commit()

        with open(cc_fixture, "r", encoding="utf-8") as f:
            content_str = f.read()
        parsed_rows, _ = csv_parser.parse(content_str)
        cat_res = categorization_agent.execute(db, user_id, parsed_rows)

        for r in cat_res["categorized_transactions"]:
            tx_id = f"tx_{uuid.uuid4().hex[:10]}"
            t_rec = Transaction(
                transaction_id=tx_id,
                user_id=user_id,
                account_id="acc_icici_cc_02",
                date=r["date"],
                description=r["description"],
                amount=r["amount"],
                direction=r["direction"],
                currency=r["currency"],
                transaction_type=r["transaction_type"],
                category=r["category"],
                category_source=r["category_source"],
                classifier_score=r["classifier_score"],
                reference=r["reference"],
                review_state=r["review_state"]
            )
            db.add(t_rec)
        db.commit()

    # 8. Seed Axis Savings Statement Fixtures
    axis_fixture = find_fixture("axis_salary_account.csv")
    upload_id_axis = "up_fixture_axis_03"
    if axis_fixture and not db.query(Upload).filter(Upload.upload_id == upload_id_axis).first():
        upload_id = "up_fixture_axis_03"
        upload = Upload(
            upload_id=upload_id,
            user_id=user_id,
            account_id="acc_axis_03",
            content_hash="hash_fixture_axis_03",
            storage_key=axis_fixture,
            original_filename="axis_salary_account.csv",
            parser_version="v1.0",
            period="2026-01 to 2026-03"
        )
        db.add(upload)
        db.commit()

        with open(axis_fixture, "r", encoding="utf-8") as f:
            content_str = f.read()
        parsed_rows, _ = csv_parser.parse(content_str)
        cat_res = categorization_agent.execute(db, user_id, parsed_rows)

        for r in cat_res["categorized_transactions"]:
            tx_id = f"tx_{uuid.uuid4().hex[:10]}"
            t_rec = Transaction(
                transaction_id=tx_id,
                user_id=user_id,
                account_id="acc_axis_03",
                date=r["date"],
                description=r["description"],
                amount=r["amount"],
                direction=r["direction"],
                currency=r["currency"],
                transaction_type=r["transaction_type"],
                category=r["category"],
                category_source=r["category_source"],
                classifier_score=r["classifier_score"],
                reference=r["reference"],
                review_state=r["review_state"]
            )
            db.add(t_rec)
        db.commit()

    # 8. Run initial Orchestrator run
    orchestrator.run_full_pipeline(db, user_id, trigger_reason="BOOTSTRAP_SEED")
    logger.info("Bootstrap seeding and initial pipeline completed successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()
