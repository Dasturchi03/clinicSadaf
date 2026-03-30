from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum
from django.db.models.signals import post_save

from apps.client.models import Client
from apps.core.choices import PaymentTypes, ReservationRequestStatuses, TransactionTypes
from apps.core.mock_seed import seed_mock_data
from apps.credit.models import Credit
from apps.medcard.models import Action, MedicalCard, Stage
from apps.notifications.models import Notification
from apps.reservation.models import Reservation, ReservationRequest
from apps.transaction.models import Transaction
from apps.user.models import User, UserSchedule
from apps.work.models import Work


SEED_TAG = "[PATIENT-PORTAL-01]"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


class Command(BaseCommand):
    help = "Create rich mock reservation/treatment history for patient.portal.01."

    def handle(self, *args, **options):
        seed_mock_data(stdout=self.stdout)
        seeder = PatientPortalHistorySeeder(stdout=self.stdout)
        summary = seeder.run()
        self.stdout.write(self.style.SUCCESS("Patient portal history seeding completed."))
        for key, value in summary.items():
            self.stdout.write(f"{key}: {value}")


class PatientPortalHistorySeeder:
    def __init__(self, stdout=None):
        self.stdout = stdout
        self.stats = Counter()
        self.patient_user: User | None = None
        self.patient_client: Client | None = None
        self.cashier: User | None = None
        self.doctors: dict[str, User] = {}
        self.works: dict[str, Work] = {}

    def run(self) -> dict[str, int]:
        with transaction.atomic():
            self._load_required_objects()
            with self._mute_realtime_signals():
                self._cleanup_existing_seed()
                self._ensure_doctor_schedules()
                self._seed_status_group("accepted", count=12)
                self._seed_status_group("in_progress", count=12)
                self._seed_status_group("completed", count=12)
        return {
            "accepted_cards": self.stats["accepted_cards"],
            "in_progress_cards": self.stats["in_progress_cards"],
            "completed_cards": self.stats["completed_cards"],
            "reservations": self.stats["reservations"],
            "reservation_requests": self.stats["reservation_requests"],
            "medical_cards": self.stats["medical_cards"],
            "actions": self.stats["actions"],
            "transactions": self.stats["transactions"],
            "credits": self.stats["credits"],
        }

    def _write(self, message: str) -> None:
        if self.stdout:
            self.stdout.write(message)

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

    def _load_required_objects(self):
        self.patient_user = User.objects.filter(username="patient.portal.01").first()
        if not self.patient_user:
            raise CommandError("patient.portal.01 user was not found.")

        self.patient_client = getattr(self.patient_user, "client_user", None)
        if not self.patient_client:
            raise CommandError("patient.portal.01 is not linked to a client.")

        self.cashier = User.objects.filter(username="cashier.mock").first()
        if not self.cashier:
            raise CommandError("cashier.mock user was not found.")

        required_doctors = {
            "therapist": "doctor.terapevt",
            "orthodontist": "doctor.ortodont",
            "surgeon": "doctor.hirurg",
            "pediatric": "doctor.pediatr",
            "radiology": "doctor.rentgen",
        }
        for key, username in required_doctors.items():
            doctor = User.objects.filter(username=username).first()
            if not doctor:
                raise CommandError(f"{username} user was not found.")
            self.doctors[key] = doctor

        required_works = [
            "Initial consultation",
            "Professional cleaning",
            "Composite filling",
            "Root canal treatment",
            "Tooth extraction",
            "Implant consultation",
            "Braces activation",
            "Bite correction plan",
            "Pediatric checkup",
            "Sealant application",
            "Panoramic X-Ray",
            "Targeted tooth X-Ray",
        ]
        for title in required_works:
            work = Work.objects.filter(work_title=title, deleted=False).first()
            if not work:
                raise CommandError(f'"{title}" work was not found.')
            self.works[title] = work

    def _cleanup_existing_seed(self):
        tagged_reservation_ids = list(
            Reservation.objects.filter(reservation_notes__startswith=SEED_TAG).values_list(
                "reservation_id", flat=True
            )
        )
        tagged_request_ids = list(
            ReservationRequest.objects.filter(
                flutter_reservation_id__startswith=SEED_TAG
            ).values_list("id", flat=True)
        )
        tagged_card_ids = list(
            MedicalCard.objects.filter(
                stage__action_stage__action_note__startswith=SEED_TAG
            )
            .distinct()
            .values_list("card_id", flat=True)
        )

        Notification.objects.filter(notification_message__startswith=SEED_TAG).delete()
        Transaction.objects.filter(comment__startswith=SEED_TAG).delete()
        Credit.objects.filter(credit_note__startswith=SEED_TAG).delete()
        ReservationRequest.objects.filter(id__in=tagged_request_ids).delete()
        Reservation.objects.filter(reservation_id__in=tagged_reservation_ids).delete()
        MedicalCard.objects.filter(card_id__in=tagged_card_ids).delete()

    def _ensure_doctor_schedules(self):
        for doctor in self.doctors.values():
            for day_index, day in enumerate(WEEKDAYS):
                UserSchedule.objects.update_or_create(
                    user=doctor,
                    day=day,
                    defaults={
                        "work_start_time": time(9, 0),
                        "work_end_time": time(18, 0),
                        "lunch_start_time": time(13, 0),
                        "lunch_end_time": time(14, 0),
                        "is_working": day_index < 5,
                        "one_time_update": False,
                    },
                )

    def _seed_status_group(self, status_name: str, *, count: int):
        for index in range(count):
            if status_name == "accepted":
                self._create_accepted_treatment(index)
            elif status_name == "in_progress":
                self._create_in_progress_treatment(index)
            else:
                self._create_completed_treatment(index)

    def _next_weekday(self, base_date: date, offset: int) -> date:
        target = base_date
        step = 1 if offset >= 0 else -1
        for _ in range(abs(offset)):
            target += timedelta(days=step)
            while target.weekday() >= 5:
                target += timedelta(days=step)
        return target

    def _time_by_index(self, index: int) -> time:
        slots = [time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 0), time(16, 0)]
        return slots[index % len(slots)]

    def _doctor_work_pairs(self):
        return [
            (self.doctors["therapist"], self.works["Composite filling"]),
            (self.doctors["therapist"], self.works["Root canal treatment"]),
            (self.doctors["orthodontist"], self.works["Braces activation"]),
            (self.doctors["surgeon"], self.works["Tooth extraction"]),
            (self.doctors["pediatric"], self.works["Sealant application"]),
            (self.doctors["radiology"], self.works["Panoramic X-Ray"]),
        ]

    def _create_reservation(self, *, group: str, item_index: int, visit_index: int, doctor: User, work: Work, reservation_date: date, start_time: time) -> Reservation:
        end_dt = datetime.combine(reservation_date, start_time) + timedelta(hours=1)
        reservation = Reservation.objects.create(
            reservation_client=self.patient_client,
            reservation_doctor=doctor,
            reservation_work=work,
            reservation_notes=f"{SEED_TAG} {group.upper()} {item_index:02d} VISIT {visit_index:02d}",
            reservation_date=reservation_date,
            reservation_start_time=start_time,
            reservation_end_time=end_dt.time(),
            is_initial=visit_index == 1,
            cancelled=False,
            cancelled_by_patient=False,
        )
        self.stats["reservations"] += 1

        ReservationRequest.objects.create(
            flutter_reservation_id=f"{SEED_TAG.lower()}-{group}-{item_index:02d}-{visit_index:02d}",
            reservation=reservation,
            client=self.patient_client,
            doctor=doctor,
            reservation_work=work,
            status=ReservationRequestStatuses.APPROVED_BY_PATIENT,
            doctor_name=doctor.full_name(),
            note=f"{SEED_TAG} Request {group} {item_index:02d}/{visit_index:02d}",
            date=reservation_date,
            time=start_time,
        )
        self.stats["reservation_requests"] += 1
        return reservation

    def _create_card(self, *, group: str, item_index: int) -> MedicalCard:
        card = MedicalCard.objects.create(
            client=self.patient_client,
            card_price=0,
            card_discount_price=0,
            card_discount_percent=0,
            card_is_done=False,
            card_is_paid=False,
            card_is_cancelled=False,
            deleted=False,
            archive=False,
        )
        self.stats["medical_cards"] += 1
        return card

    def _add_action(self, *, card: MedicalCard, stage_index: int, doctor: User, work: Work, reservation: Reservation, is_done: bool, action_note: str, price: float | None = None) -> Action:
        tooth_numbers = ["16", "21", "24", "36", "46", "11", "14", "26", "31", "41", "55", "64"]
        tooth = self._pick_tooth(tooth_numbers[stage_index % len(tooth_numbers)])
        stage = Stage.objects.create(
            tooth=tooth,
            card=card,
            stage_created_by=self.cashier,
            stage_index=stage_index,
            stage_is_done=is_done,
            stage_is_paid=False,
            stage_is_cancelled=False,
            deleted=False,
            archive=False,
        )
        action_price = price if price is not None else work.work_basic_price
        action = Action.objects.create(
            action_stage=stage,
            action_work=work,
            action_doctor=doctor,
            action_created_by=self.cashier,
            action_date=reservation,
            action_note=action_note,
            action_quantity=1,
            action_price=action_price,
            action_price_type="Basic",
            action_is_done=is_done,
            action_is_paid=False,
            action_is_cancelled=False,
            action_finished_at=datetime.combine(reservation.reservation_date, reservation.reservation_end_time)
            if is_done
            else None,
            deleted=False,
            archive=False,
        )
        self.stats["actions"] += 1
        return action

    def _pick_tooth(self, tooth_number: str):
        from apps.medcard.models import Tooth

        tooth = Tooth.objects.filter(tooth_number=tooth_number).first()
        if tooth:
            return tooth
        return Tooth.objects.order_by("tooth_id").first()

    def _sync_card_state(self, card: MedicalCard, *, finished_at=None):
        actions = list(Action.objects.filter(action_stage__card=card))
        total_price = sum(action.action_price or 0 for action in actions)
        done_actions = [action for action in actions if action.action_is_done]
        paid_sum = (
            Transaction.objects.filter(transaction_card=card).aggregate(
                total=Sum("transaction_sum")
            )["total"]
            or 0
        )
        card.card_price = total_price
        card.card_discount_price = total_price
        card.card_is_done = bool(actions) and len(done_actions) == len(actions)
        card.card_is_paid = paid_sum >= total_price and total_price > 0
        card.card_finished_at = finished_at if card.card_is_done else None
        card.save(
            update_fields=[
                "card_price",
                "card_discount_price",
                "card_is_done",
                "card_is_paid",
                "card_finished_at",
            ]
        )

    def _create_transaction(self, *, card: MedicalCard, action: Action | None, amount: float, transaction_type: str, comment: str):
        Transaction.objects.create(
            transaction_type=transaction_type,
            transaction_payment_type=PaymentTypes.CASH,
            transaction_client=self.patient_client,
            transaction_user=self.cashier,
            transaction_card=card,
            transaction_action=action,
            transaction_sum=amount,
            transaction_action_price=action.action_price if action else amount,
            transaction_work_basic_price=action.action_work.work_basic_price if action and action.action_work else amount,
            comment=comment,
        )
        self.stats["transactions"] += 1

    def _create_credit(self, *, card: MedicalCard, action: Action, note: str):
        Credit.objects.create(
            credit_client=self.patient_client,
            credit_card=card,
            credit_action=action,
            credit_user=action.action_doctor,
            credit_sum=action.action_price,
            credit_price=action.action_price,
            credit_type="Basic",
            credit_note=note,
            credit_is_paid=False,
        )
        self.stats["credits"] += 1

    def _create_accepted_treatment(self, index: int):
        doctor, work = self._doctor_work_pairs()[index % len(self._doctor_work_pairs())]
        visit_date = self._next_weekday(date.today(), index + 1)
        reservation = self._create_reservation(
            group="accepted",
            item_index=index,
            visit_index=1,
            doctor=doctor,
            work=work,
            reservation_date=visit_date,
            start_time=self._time_by_index(index),
        )
        card = self._create_card(group="accepted", item_index=index)
        self._add_action(
            card=card,
            stage_index=0,
            doctor=doctor,
            work=work,
            reservation=reservation,
            is_done=False,
            action_note=f"{SEED_TAG} accepted action {index:02d}",
        )
        self._sync_card_state(card)
        self.stats["accepted_cards"] += 1

    def _create_in_progress_treatment(self, index: int):
        doctor, work = self._doctor_work_pairs()[index % len(self._doctor_work_pairs())]
        follow_up_work = self._doctor_work_pairs()[(index + 1) % len(self._doctor_work_pairs())][1]
        first_date = self._next_weekday(date.today(), -(index + 3))
        second_date = self._next_weekday(date.today(), index + 2)

        first_reservation = self._create_reservation(
            group="in-progress",
            item_index=index,
            visit_index=1,
            doctor=doctor,
            work=work,
            reservation_date=first_date,
            start_time=self._time_by_index(index),
        )
        second_reservation = self._create_reservation(
            group="in-progress",
            item_index=index,
            visit_index=2,
            doctor=doctor,
            work=follow_up_work,
            reservation_date=second_date,
            start_time=self._time_by_index(index + 1),
        )
        card = self._create_card(group="in_progress", item_index=index)
        first_action = self._add_action(
            card=card,
            stage_index=0,
            doctor=doctor,
            work=work,
            reservation=first_reservation,
            is_done=True,
            action_note=f"{SEED_TAG} in-progress action done {index:02d}",
        )
        second_action = self._add_action(
            card=card,
            stage_index=1,
            doctor=doctor,
            work=follow_up_work,
            reservation=second_reservation,
            is_done=False,
            action_note=f"{SEED_TAG} in-progress action pending {index:02d}",
        )
        self._create_transaction(
            card=card,
            action=first_action,
            amount=first_action.action_price,
            transaction_type=TransactionTypes.PARTIALLY_PAY_FOR_ACTION,
            comment=f"{SEED_TAG} partial payment in-progress {index:02d}",
        )
        if index % 2 == 0:
            self._create_credit(
                card=card,
                action=second_action,
                note=f"{SEED_TAG} credit in-progress {index:02d}",
            )
        self._sync_card_state(card)
        self.stats["in_progress_cards"] += 1

    def _create_completed_treatment(self, index: int):
        doctor, work = self._doctor_work_pairs()[index % len(self._doctor_work_pairs())]
        second_doctor, second_work = self._doctor_work_pairs()[(index + 2) % len(self._doctor_work_pairs())]
        first_date = self._next_weekday(date.today(), -(index + 20))
        second_date = self._next_weekday(date.today(), -(index + 10))

        first_reservation = self._create_reservation(
            group="completed",
            item_index=index,
            visit_index=1,
            doctor=doctor,
            work=work,
            reservation_date=first_date,
            start_time=self._time_by_index(index),
        )
        second_reservation = self._create_reservation(
            group="completed",
            item_index=index,
            visit_index=2,
            doctor=second_doctor,
            work=second_work,
            reservation_date=second_date,
            start_time=self._time_by_index(index + 2),
        )
        card = self._create_card(group="completed", item_index=index)
        first_action = self._add_action(
            card=card,
            stage_index=0,
            doctor=doctor,
            work=work,
            reservation=first_reservation,
            is_done=True,
            action_note=f"{SEED_TAG} completed action 1 {index:02d}",
        )
        second_action = self._add_action(
            card=card,
            stage_index=1,
            doctor=second_doctor,
            work=second_work,
            reservation=second_reservation,
            is_done=True,
            action_note=f"{SEED_TAG} completed action 2 {index:02d}",
        )
        self._create_transaction(
            card=card,
            action=first_action,
            amount=first_action.action_price,
            transaction_type=TransactionTypes.PAY_FOR_ACTION,
            comment=f"{SEED_TAG} payment completed first {index:02d}",
        )
        self._create_transaction(
            card=card,
            action=second_action,
            amount=second_action.action_price,
            transaction_type=TransactionTypes.PAY_FOR_ACTION,
            comment=f"{SEED_TAG} payment completed second {index:02d}",
        )
        self._sync_card_state(
            card,
            finished_at=datetime.combine(second_reservation.reservation_date, second_reservation.reservation_end_time),
        )
        self.stats["completed_cards"] += 1
