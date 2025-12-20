import django_filters as filters
from apps.transaction.models import Transaction


# filters filter
class TransactionFilterSet(filters.FilterSet):
    
    class Meta:
        model = Transaction
        fields = ["transaction_type", "transaction_client"]



        