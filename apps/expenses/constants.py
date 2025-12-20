from django.utils.translation import gettext_lazy as _

# financial report titles
FINANCIAL_REPORT_TITLE_REFUND = "REFUND"
FINANCIAL_REPORT_TITLE_REFILL_BALANCE = "REFILL_BALANCE"
FINANCIAL_REPORT_TITLES = {
    FINANCIAL_REPORT_TITLE_REFUND: "Возврат",
    FINANCIAL_REPORT_TITLE_REFILL_BALANCE: "Пополнение баланса",
}

# income type titles
INCOME_TYPE_TITLE = "INCOME_TYPE"
INCOME_TYPE_TITLE_REFILL_BALANCE = "REFILL_BALANCE"
INCOME_TYPE_TITLE_PAY_CREDIT = "PAY_CREDIT"
INCOME_TYPE_TITLE_PAY_MEDICAL_CARD = "PAY_MEDICAL_CARD"
INCOME_TYPE_TITLES = {
    # types of which operations balance refill was received, such as: cash, terminal and etc.
    INCOME_TYPE_TITLE: "Тип оплат",
    INCOME_TYPE_TITLE_REFILL_BALANCE: "Пополнение баланса",
    INCOME_TYPE_TITLE_PAY_CREDIT: "Погашение кредита",
    INCOME_TYPE_TITLE_PAY_MEDICAL_CARD: "Оплата по медкарте",
}

# expense type titles
EXPENSE_TYPE_TITLE_REFUND = "REFUND"
EXPENSE_TYPE_TITLES = {EXPENSE_TYPE_TITLE_REFUND: "Возврат"}
