from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionTypes(models.TextChoices):
    GIVE_CREDIT = "give_credit", _("Give credit")  # Выдача кредита
    PAID_CREDIT = "paid_credit", _("Paid credit")  # Погашение кредита
    VIP_CREDIT = "vip_credit", _("Vip credit")  # Вип кредита
    PARTIALLY_PAY_CREDIT = "partial_pay_credit", _(
        "Partially paid credit"
    )  # Частичная погашение кредита
    FORGIVE_CREDIT = "forgive_credit", _("Forgiven credit")  # Прощение кредита
    PAY_FOR_ACTION = "pay_for_action", _(
        "Payment for medical card action"
    )  # Оплата за работу
    PARTIALLY_PAY_FOR_ACTION = "partial_pay_for_action", _(
        "Partial payment for medical card action"
    )  # Оплата за работу частично
    REFILL_CLIENT_BALANCE = "refill_client_balance", _(
        "Refilled client balance"
    )  # Пополнение баланса клиента
    REFUND_CLIENT_BALANCE = "refund_client_balance", _(
        "Refunded client balance"
    )  # Возврат с баланса клиента


class PaymentTypes(models.TextChoices):
    CASH = "cash", _("Cash")
    ONLINE_TRANSFER = "online_transfer", _("Online transfer")
    TERMINAL = "terminal", _("Card")
    ANOTHER = "another", _("Another")


class HepatitisTypes(models.TextChoices):
    B = "B", "B"
    С = "С", "С"
    NO = "no", _("No")


class GenderTypes(models.TextChoices):
    MALE = "Male", _("Male")
    FEMALE = "Female", _("Female")


class ReservationRequestStatuses(models.TextChoices):
    DRAFT = "draft", _("Draft")
    APPROVED = "approved", _("Approved")
    CANCELLED = "cancelled", _("Cancelled")
    APPROVED_BY_PATIENT = "approved_by_patient", _("Approved by patient")
    CANCELLED_BY_PATIENT = "cancelled_by_patient", _("Cancelled by patient")


class ClientTypes(models.TextChoices):
    VIP = "Vip", "Vip"
    BASIC = "Basic", _("Basic")


class ArticleTypes(models.TextChoices):
    GENERAL_INFO = "general_info", _("General information")
    ACHIEVEMENTS = "achievements", _("Our achievements")
    LABORATORY = "laboratory", _("Laboratory")
    COMMENTS = "comments", _("Comments")

    NEWS = "news", _("News")


# TRANSACTION_TYPES = (
#     ("Give credit", "Give credit"),                         # Выдача кредита
#     ("Paid credit", "Paid credit"),                         # Погашение кредита
#     ("Vip credit", "Vip credit"),                           # Вип кредита
#     ("Partial pay credit", "Partial pay credit"),           # Частичная погашение кредита
#     ("Forgive credit", "Forgive credit"),                   # Прощение кредита
#     ("Pay for action", "Pay for action"),                   # Оплата за работу
#     ("Partial pay for action", "Pay for action"),           # Оплата за работу частично
#     ("Refund credit", "Refund credit"),                     # Возврат денег
#     ("Refill client balance", "Refill client balance"),     # Пополнение баланса клиента
#     ("Refund client balance", "Refund client balance"),     # Возврат с баланса клиента
# )

# PAYMENT_TYPE = (
#         ("Cash", "Cash"),
#         ("Online transfer", "Online transfer"),
#         ("Terminal", "Terminal"),
#         ("Another", "Another")
#     )
