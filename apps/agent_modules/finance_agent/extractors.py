from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "invoice_question": ["invoice", "bill", "billing", "statement"],
        "payment_reminder": ["payment", "pay", "overdue", "due date", "reminder"],
        "expense_question": ["expense", "receipt", "reimbursement", "category"],
        "bookkeeping_request": ["bookkeeping", "ledger", "accounts", "reconcile"],
        "tax_question": ["tax", "vat", "gst", "deduction", "filing"],
    },
    need_keywords={
        "invoice": "Invoice inquiry",
        "payment": "Payment inquiry",
        "expense": "Expense inquiry",
    },
)
