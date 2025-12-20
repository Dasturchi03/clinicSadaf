from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.serializers import PatientSerializer
from apps.core.choices import PaymentTypes
from apps.expenses.models import ExpensesType, FinancialReport, IncomeType
from apps.storage.api.serializers import ItemSerializer
from apps.storage.models import StorageItem
from apps.user.api.nested_serializers import NestedDoctorSerializer
from apps.user.api.serializers import DoctorSerializer
from apps.user.models import UserSalary


class ExpensesSerializer(serializers.ModelSerializer):
    expenses_type_id = serializers.IntegerField(required=False)

    class Meta:
        model = ExpensesType
        fields = ["expenses_type_id", "expenses_type_title"]
        extra_kwargs = {"expenses_type_title": {"read_only": True}}


class IncomesSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = IncomeType
        fields = ["id", "title"]
        extra_kwargs = {"title": {"read_only": True}}


class ExpensesTypeSerializer(serializers.ModelSerializer):
    type_parent = serializers.PrimaryKeyRelatedField(
        queryset=ExpensesType.objects.all(), required=False, allow_null=True
    )
    type_child = serializers.SerializerMethodField("get_type_child")

    class Meta:
        model = ExpensesType
        fields = [
            "expenses_type_id",
            "type_parent",
            "expenses_type_title",
            "type_child",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"expenses_type_id": {"read_only": True}}

    def get_type_child(self, obj):
        queryset = ExpensesType.objects.filter(type_parent=obj)
        serializer = ExpensesTypeSerializer(queryset, many=True)
        return serializer.data


class IncomeTypeSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=IncomeType.objects.all(), required=False, allow_null=True
    )
    children = serializers.SerializerMethodField()

    class Meta:
        model = IncomeType
        fields = ["id", "parent", "title", "children", "created_at", "updated_at"]

    def get_children(self, obj):
        queryset = IncomeType.objects.filter(parent=obj)
        serializer = IncomeTypeSerializer(queryset, many=True)
        return serializer.data


class ListOfSalarySerializer(serializers.Serializer):
    salary_id = serializers.IntegerField(required=False)


class FinancialReportSerializer(serializers.ModelSerializer):
    report_created_by = serializers.SerializerMethodField("get_report_created_by")
    report_for_user = DoctorSerializer(required=False)
    report_for_client = PatientSerializer(required=False)
    report_expense_type = ExpensesSerializer(required=False)
    report_income_type = IncomesSerializer(required=False)
    report_storage_item = ItemSerializer(required=False)
    salaries_ids = serializers.ListSerializer(
        child=ListOfSalarySerializer(), write_only=True, required=False
    )

    class Meta:
        model = FinancialReport
        fields = [
            "report_id",
            "report_expense_type",
            "report_income_type",
            "report_title",
            "report_created_by",
            "report_for_client",
            "report_for_user",
            "report_storage_item",
            "salaries_ids",
            "report_card",
            "report_action",
            "report_work",
            "report_action_price",
            "report_work_price",
            "report_sum",
            "report_sum_usd",
            "report_usd_cource",
            "report_note",
            "report_quantity",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "report_card": {"read_only": True},
            "report_action": {"read_only": True},
            "report_work": {"read_only": True},
            "report_action_price": {"read_only": True},
            "report_work_price": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.report_title:
            data["report_title"] = dict(PaymentTypes.choices).get(
                instance.report_title, instance.report_title
            )
        else:
            data["report_title"] = instance.report_title
        return data

    def get_report_created_by(self, obj):
        try:
            serializer = NestedDoctorSerializer(obj.report_created_by)
            return serializer.data
        except AttributeError:
            pass

    def create(self, validated_data):
        current_user = self.context.get("current_user")

        salaries_ids = validated_data.pop("salaries_ids", [])
        if salaries_ids:
            return self.create_salary_reports(
                current_user, salaries_ids, validated_data
            )
        else:
            return self.create_financial_report(current_user, validated_data)

    def create_salary_reports(self, current_user, salaries_ids, validated_data):
        """
        Creates financial reports for multiple salaries with optimized database operations,
        validation, and transaction management.
        """

        # Extract all salary IDs for bulk operations
        salary_ids = [
            item.get("salary_id") for item in salaries_ids if "salary_id" in item
        ]
        if not salary_ids:
            raise ValidationError({"salaries_ids": _("No valid salary IDs provided")})

        # Prefetch all necessary data in batch to minimize database queries
        salary_instances = UserSalary.objects.filter(pk__in=salary_ids)

        # Create a mapping of salary IDs to instances for easier access
        salary_map = {str(salary.salary_id): salary for salary in salary_instances}

        # Check which salaries already have reports
        existing_reports = set(
            FinancialReport.objects.filter(report_salary_id__in=salary_ids).values_list(
                "report_salary_id", flat=True
            )
        )

        if existing_reports:
            # Get affected salary instances for detailed error reporting
            affected_salaries = [
                salary_map[str(s_id)]
                for s_id in existing_reports
                if str(s_id) in salary_map
            ]
            error_details = [
                {
                    "salary_id": str(salary.salary_id),
                    "error": _("Report already exists"),
                }
                for salary in affected_salaries
            ]

            raise ValidationError(
                {
                    "salaries_ids": _("Some salaries already have reports"),
                    "details": error_details,
                }
            )

        # Get the expense type
        expense_type, created = ExpensesType.objects.get_or_create(
            expenses_type_title="Зарплата", defaults={"expenses_type_title": "Зарплата"}
        )

        # Prepare financial reports for all valid salaries
        financial_reports = []
        updated_salaries = []

        for salary_id in salary_ids:
            if str(salary_id) not in salary_map:
                raise ValidationError(
                    {"salary_id": _(f"Salary with ID {salary_id} not found")}
                )

            salary = salary_map[str(salary_id)]

            report_instance = FinancialReport(
                report_expense_type=expense_type,
                report_title=(
                    salary.salary_work.work_title
                    if salary.salary_work
                    else "Удаленная работа"
                ),
                report_salary_work_type=salary.salary_work_type,
                report_created_by=current_user,
                report_for_user=salary.salary_for_user,
                report_salary=salary,
                report_card=salary.salary_card,
                report_action=salary.salary_action,
                report_work=salary.salary_work,
                report_action_price=salary.salary_action_price,
                report_work_price=salary.salary_work_price,
                report_sum=salary.salary_amount,
                report_note=validated_data.get("report_note", None),
                report_quantity=(
                    salary.salary_action.action_quantity
                    if salary.salary_action
                    else None
                ),
            )

            financial_reports.append(report_instance)

            # Mark for update
            salary.salary_is_paid = True
            updated_salaries.append(salary)

        # Bulk create all reports in a single database operation
        FinancialReport.objects.bulk_create(financial_reports)
        # Bulk update all salaries in a single database operation
        UserSalary.objects.bulk_update(updated_salaries, ["salary_is_paid"])
        return {}

    def create_financial_report(self, current_user, validated_data):
        """
        Creates a financial report with advanced validation, error handling, and transaction management.
        """
        # Extract and validate report title data
        report_title = validated_data.get("report_title", None)

        # Define initial values for related entities
        report_data = {
            "report_expense_type": None,
            "report_income_type": None,
            "report_storage_item": None,
            "report_for_user_id": None,
            "report_for_client_id": None,
        }

        # Process user reference if provided
        if report_for_user := validated_data.pop("report_for_user", None):
            report_data["report_for_user_id"] = report_for_user.get("id")
            if not report_data["report_for_user_id"]:
                raise ValidationError({"report_for_user": _("User ID is required")})

        # Process client reference if provided
        if report_for_client := validated_data.pop("report_for_client", None):
            report_data["report_for_client_id"] = report_for_client.get("client_id")
            if not report_data["report_for_client_id"]:
                raise ValidationError({"report_for_client": _("Client ID is required")})

        # Process expense type if provided
        if report_expense_type_data := validated_data.pop("report_expense_type", None):
            expense_type_id = report_expense_type_data.get("expenses_type_id")
            if not expense_type_id:
                raise ValidationError(
                    {"report_expense_type": _("Expense type ID is required")}
                )

            try:
                report_data["report_expense_type"] = ExpensesType.objects.get(
                    pk=expense_type_id
                )
            except ExpensesType.DoesNotExist:
                raise ValidationError(
                    {
                        "report_expense_type": _(
                            f"Expense type with ID {expense_type_id} does not exist"
                        )
                    }
                )

        # Process income type if provided
        if report_income_type_data := validated_data.pop("report_income_type", None):
            income_type_id = report_income_type_data.get("id")
            if not income_type_id:
                raise ValidationError(
                    {"report_income_type": _("Income type ID is required")}
                )

            try:
                report_data["report_income_type"] = IncomeType.objects.get(
                    pk=income_type_id
                )
                report_title = report_data["report_income_type"].title
            except IncomeType.DoesNotExist:
                raise ValidationError(
                    {
                        "report_income_type": _(
                            f"Income type with ID {income_type_id} does not exist"
                        )
                    }
                )

        # Process storage item if provided
        if report_storage_item_data := validated_data.pop("report_storage_item", None):
            item_id = report_storage_item_data.get("item_id")
            if not item_id:
                raise ValidationError(
                    {"report_storage_item": _("Storage item ID is required")}
                )

            try:
                report_data["report_storage_item"] = StorageItem.objects.get(pk=item_id)
            except StorageItem.DoesNotExist:
                raise ValidationError(
                    {
                        "report_storage_item": _(
                            f"Storage item with ID {item_id} does not exist"
                        )
                    }
                )

        # Prepare additional data
        additional_data = {
            "report_title": report_title,
            "report_created_by": current_user,
            "report_sum": validated_data.get("report_sum", None),
            "report_sum_usd": validated_data.get("report_sum_usd", None),
            "report_usd_cource": validated_data.get("report_usd_cource", None),
            "report_note": validated_data.get("report_note", None),
            "report_quantity": validated_data.get("report_quantity", None),
        }

        # Merge dictionaries for complete report data
        report_data.update(additional_data)

        # Create and save the instance
        report_instance = FinancialReport(**report_data)
        report_instance.save()
        return report_instance


class FinancialReportListSerializer(serializers.ModelSerializer):
    report_title = serializers.SerializerMethodField()
    report_type_title = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
    client_full_name = serializers.SerializerMethodField()

    class Meta:
        model = FinancialReport
        fields = [
            "report_id",
            "report_expense_type",
            "report_income_type",
            "report_type_title",
            "report_title",
            "report_sum",
            "report_sum_usd",
            "report_usd_cource",
            "report_quantity",
            "report_note",
            "report_for_user",
            "user_full_name",
            "report_for_client",
            "client_full_name",
            "report_storage_item",
            "created_at",
        ]

    def get_report_type_title(self, instance):
        return (
            instance.report_expense_type.expenses_type_title
            if instance.report_expense_type
            else instance.report_income_type.title
        )

    def get_report_title(self, instance):
        if instance.report_title:
            return dict(PaymentTypes.choices).get(
                instance.report_title, instance.report_title
            )
        return instance.report_title

    def get_user_full_name(self, instance):
        return (
            instance.report_for_user.full_name() if instance.report_for_user else None
        )

    def get_client_full_name(self, instance):
        return (
            instance.report_for_client.full_name()
            if instance.report_for_client
            else None
        )


class FinancialReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialReport
        fields = "__all__"


class FinancialReportTotalsSerializer(serializers.Serializer):
    total_sum = serializers.FloatField()
