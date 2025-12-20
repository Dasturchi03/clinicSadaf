import jwt
import urllib.parse
import datetime

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.user.models import User


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner, lifetime=None):
        self.lifetime = lifetime or settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        self.auth = JWTAuthentication()
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        if not scope.get('user') or scope['user'].is_anonymous:
            try:
                query_string = scope['query_string'].decode()
                query_params = urllib.parse.parse_qs(query_string)
                token = query_params.get('token', [None])[0]
                if token:
                    decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.SIMPLE_JWT['ALGORITHM']])
                
                current_time = datetime.datetime.now(datetime.timezone.utc)
                if 'exp' in decoded_token and decoded_token['exp'] < current_time.timestamp():
                    scope['user'] = AnonymousUser()
                else:
                    close_old_connections()
                    scope['user'] = await self.get_user(decoded_token)
                    

            except TokenError:
                scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, decoded_token):
        user_id = decoded_token.get('user_id')
        try:
            user_instance = User.objects.get(pk=user_id)
            return user_instance
        except User.DoesNotExist:
            return None
