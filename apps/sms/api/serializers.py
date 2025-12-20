import re
from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user.models import User


class SMSForUserRegistrationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(read_only=True)
    phone_number = serializers.CharField()
    user_is_active = serializers.BooleanField(read_only=True)

    def validate(self, attrs):
        phone_pattern = re.compile(settings.PHONE_PATTERN)
            
        if not phone_pattern.match(attrs["phone_number"]):
            raise ValidationError("Phone number pattern example: +998901234567")
        
        return attrs
    

class SMSForRegenerateSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user_is_active = serializers.BooleanField(read_only=True)
    
    def validate(self, attrs):
        instance = attrs.get("user_id") 
        
        if (int(instance.user_code_max_try) == 0 and timezone.now() < instance.user_code_period):
                raise ValidationError("Max tries reached, try again after 1 hour")
            
        return attrs
    
    
class VerifyUserSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    sms_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        instance = attrs.get("user_id") 
        errors = {}
        
        if instance.user_is_active:
            errors["error"] = "User is active"
        
        if instance.user_auth_code != attrs.get("sms_code"):
            errors["error"] = "Invalid sms code"
        
        if errors:
            raise ValidationError(errors)
        return attrs
    
    
class SMSForPasswordResetSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    
class SMSPasswordVerifySerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    sms_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        instance = attrs.get("user_id") 
                
        if instance.user_auth_code != attrs.get("sms_code"):
            raise ValidationError("Invalid sms code")

        return attrs
    
    
class UserPasswordResetSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    password1 = serializers.CharField(min_length=8, write_only=True)
    password2 = serializers.CharField(min_length=8, write_only=True)
        
    def validate(self, attrs):
        instance =  attrs.get("user_id") 
        errors = {}

        if instance.user_auth_code is not None:
            errors["error"] = "Verify user with password reset sms!"
            
        if attrs.get("password1") != attrs.get("password2"):
            errors["error"] = "Passwords do not match"
            
        if errors:
            raise ValidationError(errors)
        
        return attrs
    