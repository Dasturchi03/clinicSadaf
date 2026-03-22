from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.client.models import CashbackEntry, Client
from apps.core.choices import CashbackEntryTypes, LoyaltyTiers, TransactionTypes


TIER_THRESHOLDS = {
    LoyaltyTiers.BRONZE: 0,
    LoyaltyTiers.SILVER: 5_000_000,
    LoyaltyTiers.GOLD: 15_000_000,
}

TIER_CASHBACK_RATES = {
    LoyaltyTiers.BRONZE: 0.03,
    LoyaltyTiers.SILVER: 0.05,
    LoyaltyTiers.GOLD: 0.07,
}

REFERRAL_BONUS_AMOUNT = 25_000
TIER_REFERRAL_REQUIREMENTS = {
    LoyaltyTiers.BRONZE: 0,
    LoyaltyTiers.SILVER: 3,
    LoyaltyTiers.GOLD: 10,
}
ELIGIBLE_CASHBACK_TRANSACTION_TYPES = {
    TransactionTypes.PAY_FOR_ACTION,
    TransactionTypes.PARTIALLY_PAY_FOR_ACTION,
    TransactionTypes.PAID_CREDIT,
    TransactionTypes.PARTIALLY_PAY_CREDIT,
}


def get_loyalty_tier(total_spent_amount):
    if total_spent_amount >= TIER_THRESHOLDS[LoyaltyTiers.GOLD]:
        return LoyaltyTiers.GOLD
    if total_spent_amount >= TIER_THRESHOLDS[LoyaltyTiers.SILVER]:
        return LoyaltyTiers.SILVER
    return LoyaltyTiers.BRONZE


def get_cashback_rate(tier):
    return TIER_CASHBACK_RATES.get(tier, TIER_CASHBACK_RATES[LoyaltyTiers.BRONZE])


def get_next_loyalty_tier(tier):
    if tier == LoyaltyTiers.BRONZE:
        return LoyaltyTiers.SILVER
    if tier == LoyaltyTiers.SILVER:
        return LoyaltyTiers.GOLD
    return None


def build_tier_requirements(client):
    next_tier = get_next_loyalty_tier(client.loyalty_tier)
    if not next_tier:
        return {
            "current_tier": client.loyalty_tier,
            "next_tier": None,
            "goals": [],
        }

    referrals_count = client.referred_clients.count()
    required_referrals = TIER_REFERRAL_REQUIREMENTS[next_tier]
    required_spent = TIER_THRESHOLDS[next_tier]

    goals = [
        {
            "code": "invite_friends",
            "label": "Do'stlarni taklif qilish",
            "current_value": referrals_count,
            "target_value": required_referrals,
            "unit": "ta",
            "is_done": referrals_count >= required_referrals,
        },
        {
            "code": "use_services",
            "label": "Xizmatlardan foydalanish",
            "current_value": client.total_spent_amount,
            "target_value": required_spent,
            "unit": "sum",
            "is_done": client.total_spent_amount >= required_spent,
        },
    ]
    return {
        "current_tier": client.loyalty_tier,
        "next_tier": next_tier,
        "goals": goals,
    }


def sync_client_loyalty(client):
    new_tier = get_loyalty_tier(client.total_spent_amount)
    if client.loyalty_tier != new_tier:
        client.loyalty_tier = new_tier
        client.save(update_fields=["loyalty_tier"])
    return client.loyalty_tier


@transaction.atomic
def add_cashback(
    *,
    client,
    amount,
    entry_type,
    note=None,
    source_transaction=None,
    related_client=None,
):
    if amount <= 0:
        return None

    client = Client.objects.select_for_update().get(pk=client.pk)
    client.cashback_balance += amount
    client.save(update_fields=["cashback_balance"])

    return CashbackEntry.objects.create(
        client=client,
        source_transaction=source_transaction,
        related_client=related_client,
        entry_type=entry_type,
        amount=amount,
        balance_after=client.cashback_balance,
        note=note,
    )


@transaction.atomic
def reward_cashback_for_transaction(transaction_instance):
    if (
        not transaction_instance.transaction_client
        or transaction_instance.transaction_sum <= 0
        or transaction_instance.transaction_type not in ELIGIBLE_CASHBACK_TRANSACTION_TYPES
        or CashbackEntry.objects.filter(source_transaction=transaction_instance).exists()
    ):
        return None

    client = Client.objects.select_for_update().get(
        pk=transaction_instance.transaction_client_id
    )
    client.total_spent_amount += transaction_instance.transaction_sum
    client.loyalty_tier = get_loyalty_tier(client.total_spent_amount)
    client.save(update_fields=["total_spent_amount", "loyalty_tier"])

    cashback_rate = get_cashback_rate(client.loyalty_tier)
    cashback_amount = round(transaction_instance.transaction_sum * cashback_rate, 2)

    return add_cashback(
        client=client,
        amount=cashback_amount,
        entry_type=CashbackEntryTypes.EARNED,
        note=f"Cashback for transaction {transaction_instance.transaction_id}",
        source_transaction=transaction_instance,
    )


@transaction.atomic
def apply_referral_code(*, client, referral_code):
    client = Client.objects.select_for_update().get(pk=client.pk)
    if client.referred_by_id:
        raise ValidationError("Referral code has already been applied")
    if not referral_code:
        raise ValidationError({"referral_code": "Referral code is required"})

    referrer = (
        Client.objects.select_for_update()
        .filter(referral_code__iexact=referral_code.strip(), deleted=False)
        .exclude(pk=client.pk)
        .first()
    )
    if not referrer:
        raise ValidationError({"referral_code": "Referral code not found"})

    client.referred_by = referrer
    client.save(update_fields=["referred_by"])

    add_cashback(
        client=client,
        amount=REFERRAL_BONUS_AMOUNT,
        entry_type=CashbackEntryTypes.REFERRAL_BONUS,
        note=f"Referral bonus from {referrer.full_name()}",
        related_client=referrer,
    )
    add_cashback(
        client=referrer,
        amount=REFERRAL_BONUS_AMOUNT,
        entry_type=CashbackEntryTypes.REFERRAL_BONUS,
        note=f"Referral bonus for inviting {client.full_name()}",
        related_client=client,
    )
    return client
