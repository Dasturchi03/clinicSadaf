from rest_framework import serializers
from apps.report.models import MedicalCardReport
from apps.credit.models import Credit
from apps.expenses.models import FinancialReport
from apps.user.models import UserSalary
from apps.transaction.models import Transaction
from apps.medcard.models import Action
  

class MedicalCardReportActionSerializer(serializers.ModelSerializer):
    action_title = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = (
            "action_id", "action_title", "action_disease", "action_date", "action_note", "action_quantity", "action_work",
            "action_price", "action_price_type", "action_is_done", "action_is_paid", "action_created_by", "created_at"
        )
    
    def get_action_title(self, instance):
        try:
            return instance.action_work.work_title
        except:
            return None
    
        
class MedicalCardReportCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credit    
        fields = (
            "credit_id", "credit_client", "credit_price", "credit_type", "credit_note", "credit_is_paid", "credit_created_at"
        )


class MedicalCardReportFinancialReportSerializer(serializers.ModelSerializer):
    report_type_title = serializers.SerializerMethodField()

    class Meta:
        model = FinancialReport
        fields = (
            "report_id", "report_salary", "report_income_type", "report_expense_type", "report_salary_work_type",
            "report_type_title", "report_sum", "report_note", "report_quantity",
            "report_for_user", "report_for_client", "created_at"
        )

    def get_report_type_title(self, instance):
        return instance.report_expense_type.expenses_type_title if instance.report_expense_type else instance.report_income_type.title


class MedicalCardReportTransactionSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "transaction_id", "transaction_user", "transaction_client", "doctor_name", "client_name",
            "transaction_type", "transaction_payment_type", "transaction_sum",
            "transaction_benefit", "transaction_loss", "transaction_created_at"
        )

    def get_doctor_name(self, instance):
        try:
            return instance.transaction_user.full_name()
        except:
            return None
            
            
    def get_client_name(self, instance):
        try:
            return instance.transaction_client.full_name()
        except:
            return None
        
        
class MedicalCardReportSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSalary
        fields = (
            "salary_id", "salary_for_user", "salary_amount", "salary_action_price",
            "salary_is_paid", "salary_work_type", "created_at"
        )
    
    
class MedicalCardReportDetailSerializer(serializers.ModelSerializer):
    client_birthdate = serializers.SerializerMethodField()
    client_balance = serializers.SerializerMethodField()
    doctor_phone = serializers.SerializerMethodField()
    action_title = serializers.SerializerMethodField()

    action = MedicalCardReportActionSerializer(read_only=True)
    credits = MedicalCardReportCreditSerializer(many=True)
    financial_reports = MedicalCardReportFinancialReportSerializer(many=True)
    transactions = MedicalCardReportTransactionSerializer(many=True)
    salaries = MedicalCardReportSalarySerializer(many=True)

    class Meta:
        model = MedicalCardReport
        fields = (
            "client", "client_name", "client_phone", "client_birthdate", "client_balance",
            "doctor", "doctor_name", "doctor_phone", 
            "action", "action_title", "credits", "financial_reports", "transactions", "salaries", "created_at"
        )
        
    def get_client_birthdate(self, instance):
        if instance.client:
            return instance.client.client_birthdate.strftime("%d-%m-%Y")
        return None
    
    def get_client_balance(self, instance):
        if instance.client:
            return instance.client.client_balance
        return None

    def get_doctor_phone(self, instance):
        if instance.doctor:
            return instance.doctor.user_private_phone.first().private_phone
        return None
    
    def get_action_title(self, instance):
        if instance.action:
            try:
                return instance.action.action_work.work_title
            except:
                return None
        return None


class MedicalCardReportListSerializer(serializers.ModelSerializer):
    action_title = serializers.SerializerMethodField()

    class Meta:
        model = MedicalCardReport
        fields = (
            "id", "client", "client_name", "doctor", "doctor_name", "action_title", "created_at"

        )
        
    def get_action_title(self, instance):
        if instance.action:
            try:
                return instance.action.action_work.work_title
            except:
                return None
        return None