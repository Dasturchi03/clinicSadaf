import random
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth.models import Group

from rest_framework.exceptions import ValidationError

from apps.user.models import User, User_Public_Phone, User_Type
from apps.sms.tasks import send_sms_with_code
    
    
class SMSForUserRegistration():

    def __call__(self, phone_number: str) -> None:
        response: dict = None

        try:
            user_type = User_Type.objects.get(type_text="Пациент")
            user = User()
            user.user_auth_code = random.randint(100000, 999999)
            user.user_code_period = timezone.now() + timedelta(hours=1)
            user.user_is_active = False
            user.user_type = user_type
            user.save()
            phone = User_Public_Phone(user=user, public_phone=phone_number)
            phone.save()
            group = Group.objects.get(name="Пациент")
            user.groups.add(group)
            send_sms_with_code.apply_async(
                args=("Код подтверждения: {}".format(user.user_auth_code), phone_number), queue="send_sms_code", priority=10)
            
            response = {
                "message": "SMS has been sent!",
                "user_id": user.id, 
                "phone_number": phone_number, 
                "user_is_active": False, 
                }
            return response
        
        except Exception as e:
            raise ValidationError(e)
    

class SMSForRegenerate:
    def __call__(self, user: User) -> None:
        response: dict = None

        try:
            user_auth_code = random.randint(100000, 999999)
            user_code_max_try = int(user.user_code_max_try) - 1
            
            user.user_auth_code = user_auth_code
            user.user_code_max_try = user_code_max_try
            user.user_code_expire = user
            
            if user_code_max_try == 0:
                user.user_code_period = timezone.now() + timedelta(hours=1)
                
            elif user_code_max_try == -1:
                user.user_code_max_try = 2
                
            else:
                user.user_code_period = None
                user.user_code_max_try = user_code_max_try
                
            user.save()
            phone_number = User_Public_Phone.objects.filter(user=user).first().public_phone
            
            send_sms_with_code.apply_async(
                args=("Код подтверждения: {}".format(user.user_auth_code), phone_number), queue="send_sms_code", priority=10)
            
            response = {
                "message": "SMS has been sent!",
                "user_id": user.id, 
                "phone_number": phone_number, 
            }
            return response
        
        except Exception as e:
            raise ValidationError(e)
        

class SMSForPasswordReset:
    def __call__(self, user: User) -> None:
        response: dict = None

        try:
            
            user.user_auth_code = random.randint(100000, 999999)
            user.save()
            
            phone_number = User_Public_Phone.objects.filter(user=user).first().public_phone

            send_sms_with_code.apply_async(
                args=("Код подтверждения: {}".format(user.user_auth_code), phone_number), queue="send_sms_code", priority=10)

            response = {
                "message": "SMS has been sent!",
                "user_id": user.id, 
            }
            return response
        
        except Exception as e:
            raise ValidationError(e)