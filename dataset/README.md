# Personal Finance Agent - Datasets & Fixtures

This directory contains synthetic financial datasets and seed configuration files designed for testing and demonstrating the **Personal Finance Agent** system. All data represents realistic Indian banking and fintech contexts (amounts in INR, standard UPI/IMPS/NEFT transaction narratives, merchants, and dates).

---

## 1. Directory Structure

```
dataset/
├── statements/
│   ├── hdfc_bank_savings.csv     # 3-Month Primary Checking/Savings account statement (Jan-Mar 2026)
│   ├── icici_credit_card.csv     # 3-Month Credit Card statement (E-commerce, Dining, Repayments)
│   ├── axis_salary_account.csv   # 3-Month Secondary account statement (Investments & Dividends)
│   └── sample_statement.pdf      # Text-based PDF bank statement matching the normalized layout
├── training/
│   └── labeled_transactions.csv  # 470+ Labeled transaction descriptions for ML classifier training
├── seed/
│   ├── accounts.json             # Seed account definitions with initial balances
│   ├── profile.json              # Seed user profile with income, debt, and reserve targets
│   ├── budgets.json              # Monthly category budget limits
│   └── obligations.json          # Scheduled recurring income, bills, EMIs, and subscriptions
└── README.md                     # This documentation file
```

---

## 2. Statement CSV Schema

All statements strictly conform to the canonical ingestion specification:

| Column | Type | Example | Description |
|---|---|---|---|
| `date` | String (ISO 8601) | `2026-03-05` | Transaction date (`YYYY-MM-DD`). |
| `description` | String | `MONTHLY SALARY CREDIT TECHCORP LTD` | Raw transaction narrative. |
| `amount` | Decimal String | `50000.00` | Unsigned transaction amount. |
| `direction` | Enum | `CREDIT` or `DEBIT` | Cash flow direction. |
| `currency` | ISO 4217 | `INR` | Standard Indian Rupee. |
| `reference` | String | `SAL1036` | Unique transaction reference or UPI ID. |
| `balance` | Decimal String | `60500.00` | Running account balance after transaction. |

---

## 3. Pre-Configured Golden Cases & Anomalies

The primary dataset (`hdfc_bank_savings.csv`) contains the following pre-configured scenarios matching the specification:

1. **Deterministic Liquid Balance**:
   - Closing balance as of March 31, 2026 is exactly **INR 32,000.00**, aligning with the opening balance required for 30-day cash flow projections on April 1, 2026.
2. **MAD Anomaly Detection**:
   - `2026-03-26`: `MAX HEALTHCARE HOSPITAL OPD` debit of **INR 15,000.00**.
   - With baseline healthcare/retail spending centered around INR 400-800, this exceeds $\max(3m, m + 6\text{MAD}, 2000)$ and triggers the Anomaly Detection Agent.
3. **Candidate Duplicate Transaction**:
   - `2026-03-24`: Two identical debit entries of **INR 450.00** for `SWIGGY ORDER BLR` with different references (`UPI1048` and next sequence) on the same date. Triggers duplicate candidate review.
4. **Subscription Intelligence**:
   - `NETFLIX ENTERTAINMENT SUBSCRIPTION` (INR 649.00), `SPOTIFY PREMIUM MONTHLY` (INR 119.00), and `CULT FIT HEALTHCARE MEMBERSHIP` (INR 1500.00) recurring with 28–31 day intervals across January, February, and March.
5. **Budget Warning**:
   - Food & Dining budget limit is set to INR 8,000.00; actual monthly dining spend approaches 90% utilization (INR 7,200.00), triggering the 90% budget warning alert.
