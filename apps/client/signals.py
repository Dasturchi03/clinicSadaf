# from django.dispatch import Signal
# from apps.user.models import User, User_Public_Phone
# from apps.sms.tasks import send_sms_with_code


# def send_sms_for_user_registration(instance, created, **kwargs):
#     if created:
#         user = User.objects.filter(client_user=instance).first()
#         public_phone = User_Public_Phone.objects.filter(user=user).first()

#         send_sms_with_code.apply_async(
#                 args=("Логин: {}\nПароль: {}".format(user.username, "sadaf"+str(user.username)), public_phone.public_phone), queue="send_sms_code", priority=10)


# client_signal = Signal()
# client_signal.connect(receiver=send_sms_for_user_registration)