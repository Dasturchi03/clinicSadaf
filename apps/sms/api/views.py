from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.sms.api import serializers

from apps.sms.api.methods import (
    SMSForUserRegistration,
    SMSForRegenerate,
    SMSForPasswordReset
)


class SMSView(viewsets.GenericViewSet):
    queryset = None

    def get_serializer_class(self):
        if self.action == "send_sms":
            return serializers.SMSForUserRegistrationSerializer
        if self.action == "regenerate_sms":
            return serializers.SMSForRegenerateSerializer
        if self.action == "verify_user":
            return serializers.VerifyUserSerializer
        if self.action == "password_reset_sms":
            return serializers.SMSForPasswordResetSerializer
        if self.action == "verify_password_sms":
            return serializers.SMSPasswordVerifySerializer
        if self.action == "reset_password":
            return serializers.UserPasswordResetSerializer
    
    @action(methods=['post'], url_name="send_sms", detail=False, permission_classes=[])
    def send_sms(self, request, **kwargs):
        """
        Endpoint to send sms for user registration
        """
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone_number = serializer.validated_data["phone_number"]
            method = SMSForUserRegistration()
            response_data = method(phone_number)
            return Response(data=response_data)
        except Exception as e:
                raise ValidationError(e)
        
    @action(methods=['post'], url_name="regenerate_sms", detail=False, permission_classes=[])
    def regenerate_sms(self, request, **kwargs):
        """
        Endpoint to regenerate sms
        """
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user_id"]
            method = SMSForRegenerate()
            response_data = method(user)
            return Response(data=response_data)
        except Exception as e:
            raise ValidationError(e)
        
        
    @action(methods=['post'], url_name="verify_user", detail=False, permission_classes=[])
    def verify_user(self, request, **kwargs):
        """
        Endpoint to verify user by sms code
        """
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data.get("user_id")
            instance.verify_user()
            return Response({"Success": "User has been verified!", "user_id": instance.pk}, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(e)
        
        
    @action(methods=['post'], url_name="password_reset_sms", detail=False, permission_classes=[])
    def password_reset_sms(self, request, **kwargs):
        """
        Endpoint to send sms for password reset
        """
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user_id"]
            method = SMSForPasswordReset()
            response_data = method(user)
            return Response(data=response_data)
        except Exception as e:
                raise ValidationError(e)
        
        
    @action(methods=['post'], url_name="verify_password_sms", detail=False, permission_classes=[])
    def verify_password_sms(self, request, **kwargs):
        """
        Endpoint to verify password sms by sms code
        """
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data.get("user_id")
            instance.user_auth_code = None
            instance.save()
            return Response({"Success": "User password sms has been verified!", "user_id": instance.pk}, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(e)
        
        
    @action(methods=['post'], url_name="reset_password", detail=False, permission_classes=[])
    def reset_password(self, request, **kwargs):
        """
        Endpoint to save the new password
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data.get("user_id")
            instance.reset_password(user_password=serializer.validated_data.get("password1"))
            return Response({"Success": "Password has been changed!"}, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(e)
        