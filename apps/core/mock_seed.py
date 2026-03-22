from __future__ import annotations

import json
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.db.models.signals import post_save

from apps.about.models import Article, ArticleImage
from apps.client.models import Client, ClientAnamnesis, Client_Public_Phone
from apps.core.choices import (
    ArticleTypes,
    ClientTypes,
    GenderTypes,
    HepatitisTypes,
    PaymentTypes,
    ReservationRequestStatuses,
    TransactionTypes,
)
from apps.credit.models import Credit
from apps.disease.models import Disease
from apps.expenses.models import ExpensesType, FinancialReport, IncomeType
from apps.medcard.models import Action, MedicalCard, Stage, Tooth, Xray
from apps.notifications.models import Notification
from apps.report.models import MedicalCardReport
from apps.reservation.models import Reservation, ReservationRequest
from apps.specialization.models import Specialization
from apps.storage.models import Storage, StorageHistory, StorageItem
from apps.task.models import Task
from apps.transaction.models import Transaction
from apps.user.models import (
    User,
    UserSchedule,
    UserSalary,
    User_Private_Phone,
    User_Public_Phone,
    User_Type,
)
from apps.vacancies.models import (
    GenderTypes as VacancyGenderTypes,
    MaritalStatusTypes,
    Vacancy,
    VacancyApplication,
    VacancyApplicationStatus,
)
from apps.work.models import Work
from apps.category.models import Category, PrintOutCategory


SEED_TAG = "[MOCK-SEED]"
ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
    b"\xff?\x00\x05\xfe\x02\xfeA\xdd\x8d\xb1\x00\x00\x00\x00IEND\xaeB`\x82"
)
MOCK_RESUME = b"Mock resume for Clinicsadaf vacancy application.\n"


def seed_mock_data(stdout=None) -> dict[str, int]:
    seeder = MockDataSeeder(stdout=stdout)
    return seeder.run()


class MockDataSeeder:
    def __init__(self, stdout=None):
        self.stdout = stdout
        self.stats = Counter()
        self.admin_user: User | None = None
        self.user_types: dict[str, User_Type] = {}
        self.specializations: dict[str, Specialization] = {}
        self.categories: dict[str, Category] = {}
        self.print_out_categories: dict[str, PrintOutCategory] = {}
        self.diseases: dict[str, Disease] = {}
        self.income_types: dict[str, IncomeType] = {}
        self.expense_types: dict[str, ExpensesType] = {}
        self.works: dict[str, Work] = {}
        self.users: dict[str, User] = {}
        self.clients: list[Client] = []
        self.teeth: dict[str, Tooth] = {}
        self.reservations_by_client: dict[int, Reservation] = {}
        self.cards_by_client: dict[int, MedicalCard] = {}
        self.actions: list[Action] = []
        self.credits_by_action: dict[int, Credit] = {}
        self.salaries_by_action: dict[int, UserSalary] = {}
        self.reports_by_key: dict[str, FinancialReport] = {}
        self.transactions_by_key: dict[str, Transaction] = {}
        self.existing_tables: set[str] = set()

    def run(self) -> dict[str, int]:
        with transaction.atomic():
            self.existing_tables = set(connection.introspection.table_names())
            with self._mute_realtime_signals():
                self._seed_reference_data()
                self._seed_users()
                self._seed_clients()
                self._seed_teeth()
                self._seed_reservations()
                self._seed_medical_cards()
                self._seed_finance()
                self._seed_storage()
                self._seed_tasks()
                self._seed_articles()
                self._seed_vacancies()
        return self._build_summary()

    def _build_summary(self) -> dict[str, int]:
        return {
            "user_types": len(self.user_types),
            "specializations": len(self.specializations),
            "categories": len(self.categories),
            "print_out_categories": len(self.print_out_categories),
            "diseases": len(self.diseases),
            "users": len(self.users),
            "clients": len(self.clients),
            "teeth": len(self.teeth),
            "works": len(self.works),
            "reservations": len(self.reservations_by_client),
            "medical_cards": len(self.cards_by_client),
            "actions": len(self.actions),
            "credits": len(self.credits_by_action),
            "salaries": len(self.salaries_by_action),
            "financial_reports": len(self.reports_by_key),
            "transactions": len(self.transactions_by_key),
            "created_records": sum(self.stats.values()),
        }

    def _write(self, message: str) -> None:
        if self.stdout:
            self.stdout.write(message)

    def _model_table_exists(self, model) -> bool:
        return model._meta.db_table in self.existing_tables

    @contextmanager
    def _mute_realtime_signals(self):
        from apps.notifications.signals import notification_channels
        from apps.reservation.signals import reservation_channels

        disconnected_reservation = post_save.disconnect(
            receiver=reservation_channels, sender=Reservation
        )
        disconnected_notification = post_save.disconnect(
            receiver=notification_channels, sender=Notification
        )
        try:
            yield
        finally:
            if disconnected_reservation:
                post_save.connect(reservation_channels, sender=Reservation)
            if disconnected_notification:
                post_save.connect(notification_channels, sender=Notification)

    def _get_admin_user(self) -> User:
        if self.admin_user:
            return self.admin_user
        user_model = get_user_model()
        self.admin_user = user_model.objects.filter(is_superuser=True).order_by("id").first()
        if self.admin_user is None:
            self.admin_user = self._ensure_user(
                username="seed.admin",
                password="seed_admin_123",
                first_name="Seed",
                last_name="Admin",
                user_type=self.user_types["Administrator"],
                gender=GenderTypes.MALE,
                salary_percent=0,
                salary_child_percent=0,
                specializations=[],
                is_staff=True,
                is_superuser=True,
            )
        return self.admin_user

    def _find_or_create(self, model, lookup: dict, defaults: dict | None = None):
        defaults = defaults or {}
        instance = model.objects.filter(**lookup).order_by(model._meta.pk.name).first()
        created = False
        if instance is None:
            instance = model.objects.create(**lookup, **defaults)
            created = True
        else:
            changed_fields = []
            for field_name, value in defaults.items():
                if getattr(instance, field_name) != value:
                    setattr(instance, field_name, value)
                    changed_fields.append(field_name)
            if changed_fields:
                instance.save(update_fields=changed_fields)
        if created:
            self.stats[model.__name__] += 1
        return instance, created

    def _ensure_password(self, user: User, password: str) -> None:
        if not user.check_password(password):
            user.set_password(password)
            user.save(update_fields=["password"])

    def _ensure_binary_field(
        self, instance, field_name: str, filename: str, content: bytes
    ) -> None:
        field = getattr(instance, field_name)
        if field.name:
            try:
                if field.storage.exists(field.name):
                    return
            except Exception:
                pass
        field.save(filename, ContentFile(content), save=False)
        instance.save(update_fields=[field_name])

    def _seed_reference_data(self) -> None:
        for user_type_title in [
            "Administrator",
            "Doctor",
            "Cashier",
            "Operator",
            "Assistant",
            "Patient",
        ]:
            self.user_types[user_type_title], _ = self._find_or_create(
                User_Type,
                {"type_text": user_type_title},
                {"deleted": False},
            )

        for title in [
            "Therapist",
            "Orthodontist",
            "Surgeon",
            "Pediatric dentist",
            "Radiologist",
        ]:
            self.specializations[title], _ = self._find_or_create(
                Specialization,
                {"specialization_text": title},
            )

        for title in [
            "Diagnostics",
            "Therapy",
            "Surgery",
            "Orthodontics",
            "Pediatrics",
            "X-Ray",
        ]:
            self.categories[title], _ = self._find_or_create(
                Category,
                {"category_title": title},
            )

        for order_index, title in enumerate(
            ["Primary visit", "Treatment", "Control"], start=1
        ):
            self.print_out_categories[title], _ = self._find_or_create(
                PrintOutCategory,
                {"name": title},
                {"order_index": order_index},
            )

        disease_tree = {
            "Caries": ["Deep caries", "Pulpitis"],
            "Gum disease": ["Gingivitis", "Periodontitis"],
            "Bite anomaly": ["Crowding", "Open bite"],
        }
        for parent_title, children in disease_tree.items():
            parent, _ = self._find_or_create(
                Disease,
                {"disease_title": parent_title},
                {"parent": None, "archive": False, "deleted": False},
            )
            self.diseases[parent_title] = parent
            for child_title in children:
                child, _ = self._find_or_create(
                    Disease,
                    {"disease_title": child_title},
                    {"parent": parent, "archive": False, "deleted": False},
                )
                self.diseases[child_title] = child

        income_root, _ = self._find_or_create(IncomeType, {"title": "Income"})
        for title in ["Treatment income", "Client balance top-up", "Credit payment"]:
            self.income_types[title], _ = self._find_or_create(
                IncomeType,
                {"title": title},
                {"parent": income_root},
            )

        expense_root, _ = self._find_or_create(
            ExpensesType,
            {"expenses_type_title": "Expenses"},
            {"type_parent": None, "deleted": False},
        )
        for title in ["Salary payout", "Materials purchase", "Utilities"]:
            self.expense_types[title], _ = self._find_or_create(
                ExpensesType,
                {"expenses_type_title": title},
                {"type_parent": expense_root, "deleted": False},
            )

        work_definitions = [
            {
                "title": "Initial consultation",
                "type": "Common",
                "salary_type": "Fixed",
                "basic_price": 120000,
                "vip_price": 100000,
                "fixed_salary": 30000,
                "hybrid_salary": 0,
                "category": "Diagnostics",
                "print_out": "Primary visit",
                "disease": "Caries",
                "specialization": "Therapist",
            },
            {
                "title": "Professional cleaning",
                "type": "Common",
                "salary_type": "Percent",
                "basic_price": 180000,
                "vip_price": 160000,
                "fixed_salary": 0,
                "hybrid_salary": 0,
                "category": "Therapy",
                "print_out": "Treatment",
                "disease": "Gingivitis",
                "specialization": "Therapist",
            },
            {
                "title": "Composite filling",
                "type": "Tooth",
                "salary_type": "Hybrid",
                "basic_price": 350000,
                "vip_price": 300000,
                "fixed_salary": 0,
                "hybrid_salary": 40000,
                "category": "Therapy",
                "print_out": "Treatment",
                "disease": "Deep caries",
                "specialization": "Therapist",
            },
            {
                "title": "Root canal treatment",
                "type": "Tooth",
                "salary_type": "Percent",
                "basic_price": 520000,
                "vip_price": 470000,
                "fixed_salary": 0,
                "hybrid_salary": 0,
                "category": "Therapy",
                "print_out": "Treatment",
                "disease": "Pulpitis",
                "specialization": "Therapist",
            },
            {
                "title": "Tooth extraction",
                "type": "Tooth",
                "salary_type": "Fixed",
                "basic_price": 400000,
                "vip_price": 360000,
                "fixed_salary": 90000,
                "hybrid_salary": 0,
                "category": "Surgery",
                "print_out": "Treatment",
                "disease": "Periodontitis",
                "specialization": "Surgeon",
            },
            {
                "title": "Implant consultation",
                "type": "Common",
                "salary_type": "Fixed",
                "basic_price": 150000,
                "vip_price": 130000,
                "fixed_salary": 40000,
                "hybrid_salary": 0,
                "category": "Surgery",
                "print_out": "Control",
                "disease": "Gum disease",
                "specialization": "Surgeon",
            },
            {
                "title": "Braces activation",
                "type": "Tooth",
                "salary_type": "Hybrid",
                "basic_price": 280000,
                "vip_price": 250000,
                "fixed_salary": 0,
                "hybrid_salary": 50000,
                "category": "Orthodontics",
                "print_out": "Control",
                "disease": "Crowding",
                "specialization": "Orthodontist",
            },
            {
                "title": "Bite correction plan",
                "type": "Common",
                "salary_type": "Fixed",
                "basic_price": 210000,
                "vip_price": 180000,
                "fixed_salary": 50000,
                "hybrid_salary": 0,
                "category": "Orthodontics",
                "print_out": "Primary visit",
                "disease": "Open bite",
                "specialization": "Orthodontist",
            },
            {
                "title": "Pediatric checkup",
                "type": "Common",
                "salary_type": "Fixed",
                "basic_price": 110000,
                "vip_price": 90000,
                "fixed_salary": 25000,
                "hybrid_salary": 0,
                "category": "Pediatrics",
                "print_out": "Primary visit",
                "disease": "Caries",
                "specialization": "Pediatric dentist",
            },
            {
                "title": "Sealant application",
                "type": "Tooth",
                "salary_type": "Percent",
                "basic_price": 160000,
                "vip_price": 140000,
                "fixed_salary": 0,
                "hybrid_salary": 0,
                "category": "Pediatrics",
                "print_out": "Treatment",
                "disease": "Deep caries",
                "specialization": "Pediatric dentist",
            },
            {
                "title": "Panoramic X-Ray",
                "type": "Common",
                "salary_type": "Fixed",
                "basic_price": 95000,
                "vip_price": 85000,
                "fixed_salary": 20000,
                "hybrid_salary": 0,
                "category": "X-Ray",
                "print_out": "Control",
                "disease": "Caries",
                "specialization": "Radiologist",
            },
            {
                "title": "Targeted tooth X-Ray",
                "type": "Tooth",
                "salary_type": "Fixed",
                "basic_price": 70000,
                "vip_price": 60000,
                "fixed_salary": 15000,
                "hybrid_salary": 0,
                "category": "X-Ray",
                "print_out": "Control",
                "disease": "Pulpitis",
                "specialization": "Radiologist",
            },
        ]
        for item in work_definitions:
            work, _ = self._find_or_create(
                Work,
                {"work_title": item["title"]},
                {
                    "work_type": item["type"],
                    "work_salary_type": item["salary_type"],
                    "work_basic_price": item["basic_price"],
                    "work_vip_price": item["vip_price"],
                    "work_null_price": 0,
                    "work_discount_percent": 10,
                    "work_discount_price": max(item["basic_price"] - 20000, 0),
                    "work_fixed_salary_amount": item["fixed_salary"],
                    "work_hybrid_salary_amount": item["hybrid_salary"],
                    "archive": False,
                    "deleted": False,
                },
            )
            work.category.set([self.categories[item["category"]]])
            work.print_out_categories.set([self.print_out_categories[item["print_out"]]])
            work.disease.set([self.diseases[item["disease"]]])
            work.specialization.set([self.specializations[item["specialization"]]])
            self.works[item["title"]] = work

    def _ensure_user(
        self,
        *,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        user_type: User_Type,
        gender: str,
        salary_percent: int,
        salary_child_percent: int,
        specializations: list[Specialization],
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> User:
        user, _ = self._find_or_create(
            User,
            {"username": username},
            {
                "user_firstname": first_name,
                "user_lastname": last_name,
                "user_type": user_type,
                "user_gender": gender,
                "user_address": "Tashkent city",
                "user_citizenship": "UZ",
                "user_telegram": f"@{username.replace('.', '_')}",
                "user_color": "#2f855a" if user_type.type_text == "Doctor" else "#1f6feb",
                "user_on_place": True,
                "user_is_active": True,
                "user_salary_percent": salary_percent,
                "user_salary_child_percent": salary_child_percent,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "archive": False,
                "deleted": False,
            },
        )
        self._ensure_password(user, password)
        user.user_specialization.set(specializations)
        return user

    def _seed_users(self) -> None:
        self.admin_user = self._get_admin_user()

        user_definitions = [
            {
                "username": "doctor.terapevt",
                "password": "mock_doctor_123",
                "first_name": "Akmal",
                "last_name": "Karimov",
                "type": "Doctor",
                "gender": GenderTypes.MALE,
                "salary_percent": 25,
                "salary_child_percent": 20,
                "specializations": ["Therapist"],
            },
            {
                "username": "doctor.ortodont",
                "password": "mock_doctor_123",
                "first_name": "Malika",
                "last_name": "Usmonova",
                "type": "Doctor",
                "gender": GenderTypes.FEMALE,
                "salary_percent": 22,
                "salary_child_percent": 18,
                "specializations": ["Orthodontist"],
            },
            {
                "username": "doctor.hirurg",
                "password": "mock_doctor_123",
                "first_name": "Jasur",
                "last_name": "Tojiyev",
                "type": "Doctor",
                "gender": GenderTypes.MALE,
                "salary_percent": 30,
                "salary_child_percent": 0,
                "specializations": ["Surgeon"],
            },
            {
                "username": "doctor.pediatr",
                "password": "mock_doctor_123",
                "first_name": "Dilnoza",
                "last_name": "Saidova",
                "type": "Doctor",
                "gender": GenderTypes.FEMALE,
                "salary_percent": 24,
                "salary_child_percent": 24,
                "specializations": ["Pediatric dentist"],
            },
            {
                "username": "doctor.rentgen",
                "password": "mock_doctor_123",
                "first_name": "Temur",
                "last_name": "Qodirov",
                "type": "Doctor",
                "gender": GenderTypes.MALE,
                "salary_percent": 18,
                "salary_child_percent": 18,
                "specializations": ["Radiologist"],
            },
            {
                "username": "cashier.mock",
                "password": "mock_cashier_123",
                "first_name": "Zarina",
                "last_name": "Mirzayeva",
                "type": "Cashier",
                "gender": GenderTypes.FEMALE,
                "salary_percent": 0,
                "salary_child_percent": 0,
                "specializations": [],
            },
            {
                "username": "assistant.mock",
                "password": "mock_assistant_123",
                "first_name": "Sherzod",
                "last_name": "Rahimov",
                "type": "Assistant",
                "gender": GenderTypes.MALE,
                "salary_percent": 0,
                "salary_child_percent": 0,
                "specializations": [],
            },
            {
                "username": "operator.mock",
                "password": "mock_operator_123",
                "first_name": "Nigina",
                "last_name": "Tursunova",
                "type": "Operator",
                "gender": GenderTypes.FEMALE,
                "salary_percent": 0,
                "salary_child_percent": 0,
                "specializations": [],
            },
        ]
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        for index, item in enumerate(user_definitions, start=1):
            user = self._ensure_user(
                username=item["username"],
                password=item["password"],
                first_name=item["first_name"],
                last_name=item["last_name"],
                user_type=self.user_types[item["type"]],
                gender=item["gender"],
                salary_percent=item["salary_percent"],
                salary_child_percent=item["salary_child_percent"],
                specializations=[self.specializations[name] for name in item["specializations"]],
                is_staff=True,
            )
            self.users[item["username"]] = user
            self._find_or_create(
                User_Public_Phone,
                {"user": user, "public_phone": f"+998900000{index:03d}"},
                {"deleted": False},
            )
            self._find_or_create(
                User_Private_Phone,
                {"user": user, "private_phone": f"+998910000{index:03d}"},
                {"deleted": False},
            )
            for day_index, day in enumerate(weekdays):
                self._find_or_create(
                    UserSchedule,
                    {"user": user, "day": day},
                    {
                        "work_start_time": time(9, 0),
                        "work_end_time": time(18, 0),
                        "lunch_start_time": time(13, 0),
                        "lunch_end_time": time(14, 0),
                        "is_working": day_index < 5,
                        "one_time_update": False,
                    },
                )

    def _seed_clients(self) -> None:
        client_rows = [
            ("Ali", "Yusupov", date(1991, 2, 14), GenderTypes.MALE),
            ("Madina", "Rasulova", date(1988, 7, 2), GenderTypes.FEMALE),
            ("Bobur", "Meliyev", date(2002, 1, 19), GenderTypes.MALE),
            ("Sabina", "Ortiqova", date(1995, 11, 7), GenderTypes.FEMALE),
            ("Ibrohim", "Jo'rayev", date(2014, 4, 23), GenderTypes.MALE),
            ("Laylo", "Olimova", date(2012, 9, 5), GenderTypes.FEMALE),
            ("Sardor", "Azimov", date(1984, 12, 17), GenderTypes.MALE),
            ("Nilufar", "Xolmatova", date(1999, 5, 30), GenderTypes.FEMALE),
            ("Kamron", "Aliyev", date(2008, 8, 12), GenderTypes.MALE),
            ("Aziza", "Hamidova", date(1993, 3, 10), GenderTypes.FEMALE),
            ("Behruz", "Sobirov", date(1987, 6, 21), GenderTypes.MALE),
            ("Mohira", "Turg'unova", date(2016, 1, 8), GenderTypes.FEMALE),
        ]
        for index, row in enumerate(client_rows, start=1):
            firstname, lastname, birthdate, gender = row
            client_user = None
            if index <= 4:
                username = f"patient.portal.{index:02d}"
                client_user = self._ensure_user(
                    username=username,
                    password="mock_patient_123",
                    first_name=firstname,
                    last_name=lastname,
                    user_type=self.user_types["Patient"],
                    gender=gender,
                    salary_percent=0,
                    salary_child_percent=0,
                    specializations=[],
                )
                self.users[username] = client_user
            client, _ = self._find_or_create(
                Client,
                {"note": f"{SEED_TAG} CLIENT {index:02d}"},
                {
                    "client_user": client_user,
                    "client_firstname": firstname,
                    "client_lastname": lastname,
                    "client_father_name": "Mockov",
                    "client_birthdate": birthdate,
                    "client_gender": gender,
                    "client_address": "Tashkent region",
                    "client_citizenship": "UZ",
                    "client_telegram": f"@client_{index:02d}",
                    "client_type": ClientTypes.VIP if index % 3 == 0 else ClientTypes.BASIC,
                    "client_balance": 150000 if index % 4 == 0 else 0,
                    "archive": False,
                    "deleted": False,
                },
            )
            self.clients.append(client)
            self._find_or_create(
                Client_Public_Phone,
                {"client": client, "public_phone": f"+998930000{index:03d}"},
                {"deleted": False},
            )
            self._find_or_create(
                ClientAnamnesis,
                {"client": client},
                {
                    "contact_reason": "Routine dental treatment",
                    "treatment_history": "No serious contraindications. Mock patient history.",
                    "hiv": False,
                    "hepatitis": HepatitisTypes.NO,
                },
            )

    def _seed_teeth(self) -> None:
        teeth_path = Path(settings.BASE_DIR) / "teeth.json"
        teeth_payload = json.loads(teeth_path.read_text(encoding="utf-8"))
        for item in teeth_payload:
            fields = item["fields"]
            tooth, _ = self._find_or_create(
                Tooth,
                {"tooth_number": fields["tooth_number"]},
                {
                    "tooth_type": fields["tooth_type"],
                    "archive": False,
                    "deleted": False,
                },
            )
            if not tooth.tooth_image:
                tooth.tooth_image = fields["tooth_image"]
                tooth.save(update_fields=["tooth_image"])
            self._ensure_binary_field(
                tooth,
                "tooth_image",
                f"{fields['tooth_number']}.png",
                ONE_PIXEL_PNG,
            )
            self.teeth[fields["tooth_number"]] = tooth

    def _choose_work_for_client(self, client: Client, stage_index: int) -> Work:
        if client.client_birthdate.year >= 2010:
            titles = ["Pediatric checkup", "Sealant application"]
        elif client.client_type == ClientTypes.VIP:
            titles = ["Bite correction plan", "Braces activation"]
        else:
            titles = ["Composite filling", "Root canal treatment"]
        return self.works[titles[stage_index % len(titles)]]

    def _choose_doctor_for_work(self, work: Work) -> User:
        specialization = work.specialization.first()
        mapping = {
            "Therapist": "doctor.terapevt",
            "Orthodontist": "doctor.ortodont",
            "Surgeon": "doctor.hirurg",
            "Pediatric dentist": "doctor.pediatr",
            "Radiologist": "doctor.rentgen",
        }
        return self.users[mapping[specialization.specialization_text]]

    def _seed_reservations(self) -> None:
        today = date.today()
        operator = self.users["operator.mock"]
        for index, client in enumerate(self.clients, start=1):
            work = self._choose_work_for_client(client, 0)
            doctor = self._choose_doctor_for_work(work)
            reservation_date = today + timedelta(days=(index % 7) - 2)
            start_hour = 9 + (index % 6)
            reservation, _ = self._find_or_create(
                Reservation,
                {"reservation_notes": f"{SEED_TAG} RESERVATION {index:02d}"},
                {
                    "reservation_client": client,
                    "reservation_doctor": doctor,
                    "reservation_work": work,
                    "reservation_date": reservation_date,
                    "reservation_start_time": time(start_hour, 0),
                    "reservation_end_time": time(start_hour + 1, 0),
                    "is_initial": index % 2 == 0,
                    "cancelled": False,
                    "cancelled_by_patient": False,
                },
            )
            self.reservations_by_client[client.client_id] = reservation
            self._find_or_create(
                ReservationRequest,
                {"flutter_reservation_id": f"seed-reservation-request-{index:02d}"},
                {
                    "reservation": reservation if index % 2 == 0 else None,
                    "client": client,
                    "doctor": doctor,
                    "status": (
                        ReservationRequestStatuses.APPROVED
                        if index % 2 == 0
                        else ReservationRequestStatuses.DRAFT
                    ),
                    "doctor_name": doctor.full_name(),
                    "note": f"{SEED_TAG} Reservation request {index:02d}",
                    "date": reservation.reservation_date,
                    "time": reservation.reservation_start_time,
                },
            )
            self._find_or_create(
                Notification,
                {
                    "notification_receiver": doctor,
                    "notification_message": f"{SEED_TAG} Reservation assigned {index:02d}",
                },
                {
                    "notification_reservation": reservation,
                },
            )
            self._find_or_create(
                Notification,
                {
                    "notification_receiver": operator,
                    "notification_message": f"{SEED_TAG} Reservation follow-up {index:02d}",
                },
                {
                    "notification_reservation": reservation,
                },
            )

    def _seed_medical_cards(self) -> None:
        adult_teeth = ["16", "21", "24", "36", "46", "11"]
        child_teeth = ["55", "64", "74", "84", "51", "71"]
        for index, client in enumerate(self.clients, start=1):
            card, _ = self._find_or_create(
                MedicalCard,
                {"client": client},
                {
                    "card_price": 0,
                    "card_discount_price": 0,
                    "card_discount_percent": 0,
                    "card_is_done": False,
                    "card_is_paid": False,
                    "card_is_cancelled": False,
                    "archive": False,
                    "deleted": False,
                },
            )
            self.cards_by_client[client.client_id] = card
            reservation = self.reservations_by_client[client.client_id]
            tooth_numbers = child_teeth if client.client_birthdate.year >= 2010 else adult_teeth
            card_total = 0
            card_paid = True

            for stage_index in range(2):
                tooth_number = tooth_numbers[(index + stage_index) % len(tooth_numbers)]
                stage, _ = self._find_or_create(
                    Stage,
                    {"card": card, "stage_index": stage_index + 1},
                    {
                        "tooth": self.teeth[tooth_number],
                        "stage_created_by": self._get_admin_user(),
                        "stage_is_done": stage_index == 0,
                        "stage_is_paid": stage_index == 0,
                        "stage_is_cancelled": False,
                        "archive": False,
                        "deleted": False,
                    },
                )
                for action_offset in range(2):
                    work = self._choose_work_for_client(client, stage_index + action_offset)
                    doctor = self._choose_doctor_for_work(work)
                    is_paid = action_offset == 0
                    base_price = work.work_vip_price if client.client_type == ClientTypes.VIP else work.work_basic_price
                    action_price = float(base_price)
                    action, _ = self._find_or_create(
                        Action,
                        {"action_note": f"{SEED_TAG} ACTION {index:02d}-{stage_index + 1}-{action_offset + 1}"},
                        {
                            "action_stage": stage,
                            "action_work": work,
                            "action_doctor": doctor,
                            "action_created_by": self._get_admin_user(),
                            "action_disease": work.disease.first(),
                            "action_date": reservation if action_offset == 0 else None,
                            "action_quantity": 1,
                            "action_price": action_price,
                            "action_price_type": "Vip" if client.client_type == ClientTypes.VIP else "Basic",
                            "action_is_done": action_offset == 0,
                            "action_is_paid": is_paid,
                            "action_is_cancelled": False,
                            "action_finished_at": (
                                datetime.combine(reservation.reservation_date, reservation.reservation_start_time)
                                if action_offset == 0
                                else None
                            ),
                            "archive": False,
                            "deleted": False,
                        },
                    )
                    self.actions.append(action)
                    card_total += action.action_price
                    if not action.action_is_paid:
                        card_paid = False

                    if stage_index == 0 and action_offset == 0:
                        xray, _ = self._find_or_create(
                            Xray,
                            {
                                "client": client,
                                "medical_card": card,
                                "stage": stage,
                                "tooth": self.teeth[tooth_number],
                            },
                        )
                        self._ensure_binary_field(
                            xray,
                            "image",
                            f"mock-xray-{client.client_id}.png",
                            ONE_PIXEL_PNG,
                        )

            card.card_price = card_total
            card.card_discount_percent = 5 if client.client_type == ClientTypes.VIP else 0
            card.card_discount_price = max(card_total - (card_total * card.card_discount_percent / 100), 0)
            card.card_is_paid = card_paid
            card.card_is_done = any(item.action_is_done for item in Action.objects.filter(action_stage__card=card))
            card.save(
                update_fields=[
                    "card_price",
                    "card_discount_percent",
                    "card_discount_price",
                    "card_is_paid",
                    "card_is_done",
                ]
            )

    def _calculate_salary_amount(self, action: Action, doctor: User) -> float:
        work = action.action_work
        if work.work_salary_type == "Fixed":
            return float(work.work_fixed_salary_amount)
        if work.work_salary_type == "Percent":
            percent = doctor.user_salary_child_percent if action.action_stage.card.client.client_birthdate.year >= 2010 else doctor.user_salary_percent
            return round(action.action_price * percent / 100, 2)
        percent = doctor.user_salary_percent
        return round(float(work.work_hybrid_salary_amount) + action.action_price * percent / 100, 2)

    def _seed_finance(self) -> None:
        cashier = self.users["cashier.mock"]
        for index, action in enumerate(self.actions, start=1):
            client = action.action_stage.card.client
            card = action.action_stage.card
            doctor = action.action_doctor
            work = action.action_work

            salary, _ = self._find_or_create(
                UserSalary,
                {
                    "salary_for_user": doctor,
                    "salary_action": action,
                },
                {
                    "salary_card": card,
                    "salary_work": work,
                    "salary_work_type": work.work_salary_type,
                    "salary_action_price": action.action_price,
                    "salary_work_price": work.work_basic_price,
                    "salary_amount": self._calculate_salary_amount(action, doctor),
                    "salary_is_paid": action.action_is_paid and index % 3 != 0,
                },
            )
            self.salaries_by_action[action.action_id] = salary

            income_report, _ = self._find_or_create(
                FinancialReport,
                {"report_title": f"{SEED_TAG} INCOME ACTION {action.action_id}"},
                {
                    "report_income_type": self.income_types["Treatment income"],
                    "report_created_by": cashier,
                    "report_for_user": doctor,
                    "report_for_client": client,
                    "report_salary": salary,
                    "report_card": card,
                    "report_action": action,
                    "report_work": work,
                    "report_action_price": action.action_price,
                    "report_work_price": work.work_basic_price,
                    "report_sum": action.action_price if action.action_is_paid else round(action.action_price * 0.4, 2),
                    "report_sum_usd": None,
                    "report_usd_cource": None,
                    "report_note": f"{SEED_TAG} treatment income",
                    "report_salary_work_type": work.work_salary_type,
                },
            )
            self.reports_by_key[f"income-{action.action_id}"] = income_report

            transaction_sum = (
                action.action_price if action.action_is_paid else round(action.action_price * 0.4, 2)
            )
            transaction_type = (
                TransactionTypes.PAY_FOR_ACTION
                if action.action_is_paid
                else TransactionTypes.PARTIALLY_PAY_FOR_ACTION
            )
            action_transaction, _ = self._find_or_create(
                Transaction,
                {"comment": f"{SEED_TAG} ACTION PAYMENT {action.action_id}"},
                {
                    "transaction_type": transaction_type,
                    "transaction_payment_type": PaymentTypes.CASH if index % 2 else PaymentTypes.TERMINAL,
                    "transaction_client": client,
                    "transaction_receiver": None,
                    "transaction_user": cashier,
                    "updated_by": cashier,
                    "transaction_card": card,
                    "transaction_action": action,
                    "transaction_credit": None,
                    "financial_report": income_report,
                    "transaction_sum": transaction_sum,
                    "transaction_action_price": action.action_price,
                    "transaction_discount_price": max(action.action_price - transaction_sum, 0),
                    "transaction_discount_percent": 0,
                    "transaction_work_basic_price": work.work_basic_price,
                    "transaction_work_vip_price": work.work_vip_price,
                    "transaction_work_discount_price": work.work_discount_price,
                    "transaction_work_discount_percent": int(work.work_discount_percent),
                    "transaction_card_discount_price": card.card_discount_price,
                    "transaction_card_discount_percent": card.card_discount_percent,
                    "transaction_benefit": max(transaction_sum - salary.salary_amount, 0),
                    "transaction_loss": max(action.action_price - transaction_sum, 0),
                },
            )
            self.transactions_by_key[f"action-{action.action_id}"] = action_transaction

            if index % 5 == 0:
                credit, _ = self._find_or_create(
                    Credit,
                    {"credit_note": f"{SEED_TAG} CREDIT {action.action_id}"},
                    {
                        "credit_client": client,
                        "credit_card": card,
                        "credit_action": action,
                        "credit_user": cashier,
                        "credit_sum": round(action.action_price * 0.6, 2),
                        "credit_price": action.action_price,
                        "credit_type": "Vip" if client.client_type == ClientTypes.VIP else "Basic",
                        "credit_is_paid": index % 10 == 0,
                    },
                )
                self.credits_by_action[action.action_id] = credit

                credit_report, _ = self._find_or_create(
                    FinancialReport,
                    {"report_title": f"{SEED_TAG} CREDIT PAYMENT {credit.credit_id}"},
                    {
                        "report_income_type": self.income_types["Credit payment"],
                        "report_created_by": cashier,
                        "report_for_user": doctor,
                        "report_for_client": client,
                        "report_card": card,
                        "report_action": action,
                        "report_work": work,
                        "report_sum": 0 if not credit.credit_is_paid else credit.credit_price,
                        "report_note": f"{SEED_TAG} credit tracking",
                    },
                )
                self.reports_by_key[f"credit-{action.action_id}"] = credit_report

                if credit.credit_is_paid:
                    credit_transaction, _ = self._find_or_create(
                        Transaction,
                        {"comment": f"{SEED_TAG} CREDIT PAYMENT TX {credit.credit_id}"},
                        {
                            "transaction_type": TransactionTypes.PAID_CREDIT,
                            "transaction_payment_type": PaymentTypes.ONLINE_TRANSFER,
                            "transaction_client": client,
                            "transaction_receiver": None,
                            "transaction_user": cashier,
                            "updated_by": cashier,
                            "transaction_card": card,
                            "transaction_action": action,
                            "transaction_credit": credit,
                            "financial_report": credit_report,
                            "transaction_sum": credit.credit_price,
                            "transaction_action_price": credit.credit_price,
                            "transaction_discount_price": 0,
                            "transaction_discount_percent": 0,
                            "transaction_work_basic_price": work.work_basic_price,
                            "transaction_work_vip_price": work.work_vip_price,
                            "transaction_work_discount_price": 0,
                            "transaction_work_discount_percent": 0,
                            "transaction_card_discount_price": 0,
                            "transaction_card_discount_percent": 0,
                            "transaction_benefit": credit.credit_price,
                            "transaction_loss": 0,
                        },
                    )
                    self.transactions_by_key[f"credit-{credit.credit_id}"] = credit_transaction

            if index % 4 == 0:
                refill_report, _ = self._find_or_create(
                    FinancialReport,
                    {"report_title": f"{SEED_TAG} BALANCE REFILL {client.client_id}"},
                    {
                        "report_income_type": self.income_types["Client balance top-up"],
                        "report_created_by": cashier,
                        "report_for_client": client,
                        "report_sum": 100000,
                        "report_note": f"{SEED_TAG} client balance refill",
                    },
                )
                self.reports_by_key[f"refill-{client.client_id}"] = refill_report
                refill_transaction, _ = self._find_or_create(
                    Transaction,
                    {"comment": f"{SEED_TAG} BALANCE REFILL TX {client.client_id}"},
                    {
                        "transaction_type": TransactionTypes.REFILL_CLIENT_BALANCE,
                        "transaction_payment_type": PaymentTypes.CASH,
                        "transaction_client": client,
                        "transaction_receiver": None,
                        "transaction_user": cashier,
                        "updated_by": cashier,
                        "financial_report": refill_report,
                        "transaction_sum": 100000,
                        "transaction_action_price": 100000,
                        "transaction_discount_price": 0,
                        "transaction_discount_percent": 0,
                        "transaction_work_basic_price": 0,
                        "transaction_work_vip_price": 0,
                        "transaction_work_discount_price": 0,
                        "transaction_work_discount_percent": 0,
                        "transaction_card_discount_price": 0,
                        "transaction_card_discount_percent": 0,
                        "transaction_benefit": 100000,
                        "transaction_loss": 0,
                    },
                )
                self.transactions_by_key[f"refill-{client.client_id}"] = refill_transaction

            card_report, _ = self._find_or_create(
                MedicalCardReport,
                {"action": action},
                {
                    "client": client,
                    "client_name": client.full_name(),
                    "client_phone": client.client_public_phone.first().public_phone if client.client_public_phone.exists() else None,
                    "doctor": doctor,
                    "doctor_name": doctor.full_name(),
                    "updated_by": cashier,
                },
            )
            related_credits = []
            if action.action_id in self.credits_by_action:
                related_credits.append(self.credits_by_action[action.action_id])
            card_report.credits.set(related_credits)
            card_report.financial_reports.set(
                [
                    report
                    for key, report in self.reports_by_key.items()
                    if str(action.action_id) in key
                ]
            )
            card_report.transactions.set(
                [
                    tx
                    for key, tx in self.transactions_by_key.items()
                    if str(action.action_id) in key
                ]
            )
            card_report.salaries.set([salary])

    def _seed_storage(self) -> None:
        assistant = self.users["assistant.mock"]
        items = [
            ("Composite material", "pack", 14),
            ("Anesthetic", "ampule", 50),
            ("Disposable gloves", "box", 22),
            ("X-Ray film", "piece", 70),
        ]
        for index, (name, measure, quantity) in enumerate(items, start=1):
            item, _ = self._find_or_create(
                StorageItem,
                {"item_name": name},
                {
                    "item_created_by": assistant,
                    "item_measure": measure,
                    "deleted": False,
                },
            )
            storage, _ = self._find_or_create(
                Storage,
                {"storage_item": item},
                {
                    "storage_created_by": assistant,
                    "storage_item_measure": measure,
                    "storage_quantity": quantity,
                    "deleted": False,
                },
            )
            self._find_or_create(
                StorageHistory,
                {
                    "storage_history_item": storage,
                    "storage_history_type": "add_quantity",
                    "storage_history_item_quantity": quantity,
                },
                {
                    "storage_history_created_by": assistant,
                    "storage_history_created_for": self.users["cashier.mock"],
                    "storage_history_item_measure": measure,
                    "storage_history_item_quantity_before": 0,
                },
            )
            storage_report, _ = self._find_or_create(
                FinancialReport,
                {"report_title": f"{SEED_TAG} STORAGE {index:02d}"},
                {
                    "report_expense_type": self.expense_types["Materials purchase"],
                    "report_created_by": assistant,
                    "report_storage_item": item,
                    "report_sum": quantity * 25000,
                    "report_quantity": quantity,
                    "report_note": f"{SEED_TAG} stock refill",
                },
            )
            self.reports_by_key[f"storage-{index}"] = storage_report

    def _seed_tasks(self) -> None:
        task_rows = [
            (
                self._get_admin_user(),
                self.users["operator.mock"],
                "Call back patients with overdue reservations",
            ),
            (
                self.users["cashier.mock"],
                self.users["assistant.mock"],
                "Check material balances before Monday",
            ),
            (
                self.users["doctor.terapevt"],
                self.users["doctor.rentgen"],
                "Review X-Ray results for therapy patients",
            ),
            (
                self.users["operator.mock"],
                self.users["doctor.ortodont"],
                "Confirm tomorrow orthodontic visits",
            ),
        ]
        for index, (task_from, task_to, description) in enumerate(task_rows, start=1):
            self._find_or_create(
                Task,
                {"task_description": f"{SEED_TAG} {description}"},
                {
                    "task_from": task_from,
                    "task_to": task_to,
                    "task_priority": "Обычный" if index % 2 else "Высокий",
                    "task_deadline": datetime.now() + timedelta(days=index),
                    "task_finished": False,
                    "archive": False,
                    "deleted": False,
                },
            )

    def _seed_articles(self) -> None:
        article_rows = [
            (ArticleTypes.GENERAL_INFO, "Clinic overview"),
            (ArticleTypes.ACHIEVEMENTS, "Key achievements"),
            (ArticleTypes.LABORATORY, "Laboratory services"),
            (ArticleTypes.COMMENTS, "Patient reviews"),
            (ArticleTypes.NEWS, "Clinic news"),
        ]
        for index, (article_type, title) in enumerate(article_rows, start=1):
            article, _ = self._find_or_create(
                Article,
                {
                    "article_type": article_type,
                    "article_title": f"{SEED_TAG} {title}",
                },
                {
                    "article_body": f"{SEED_TAG} Mock content for {title.lower()} section.",
                },
            )
            if index <= 2:
                image, _ = self._find_or_create(ArticleImage, {"article": article})
                self._ensure_binary_field(
                    image,
                    "article_image",
                    f"mock-article-{index}.png",
                    ONE_PIXEL_PNG,
                )

    def _seed_vacancies(self) -> None:
        if not self._model_table_exists(Vacancy) or not self._model_table_exists(
            VacancyApplication
        ):
            self._write(
                "Skipping vacancy seeding because vacancies tables are missing. "
                "Create migrations for apps.vacancies and migrate to enable it."
            )
            return
        vacancy_rows = [
            (
                "Front desk administrator",
                "Work with patient calls and front-desk flow.",
                Decimal("5000000.00"),
                Decimal("7000000.00"),
            ),
            (
                "Dental assistant",
                "Support doctors during procedures and prepare tools.",
                Decimal("4000000.00"),
                Decimal("5500000.00"),
            ),
        ]
        for index, (title, description, salary_from, salary_to) in enumerate(vacancy_rows, start=1):
            vacancy, _ = self._find_or_create(
                Vacancy,
                {"title": f"{SEED_TAG} {title}"},
                {
                    "description": description,
                    "requirements": "Responsible, punctual, basic computer skills.",
                    "responsibilities": "Support daily clinic operations.",
                    "conditions": "Official employment, meals included.",
                    "salary_from": salary_from,
                    "salary_to": salary_to,
                    "address": "Tashkent, Chilonzor",
                    "phone": "+998900001111",
                    "email": "hr@clinicsadaf.local",
                    "deadline": date.today() + timedelta(days=30),
                    "is_active": True,
                    "sort_order": index,
                },
            )
            application, _ = self._find_or_create(
                VacancyApplication,
                {
                    "vacancy": vacancy,
                    "phone": f"+998940000{index:03d}",
                },
                {
                    "first_name": "Applicant",
                    "last_name": f"Mock {index}",
                    "middle_name": "Candidate",
                    "email": f"applicant{index}@example.com",
                    "address": "Tashkent",
                    "birth_date": date(1998, index, min(index + 10, 28)),
                    "gender": VacancyGenderTypes.FEMALE if index % 2 == 0 else VacancyGenderTypes.MALE,
                    "marital_status": MaritalStatusTypes.SINGLE,
                    "message": f"{SEED_TAG} Vacancy application {index}",
                    "status": VacancyApplicationStatus.NEW if index == 1 else VacancyApplicationStatus.IN_REVIEW,
                },
            )
            self._ensure_binary_field(
                application,
                "resume_file",
                f"mock-resume-{index}.txt",
                MOCK_RESUME,
            )
