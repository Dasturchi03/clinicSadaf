import requests
import json
from django.core.cache import cache
from django.conf import settings
        
        
def get_access_token():
    try:
        
        token = cache.get('cache_sms')

        if token is None:
            headers = {
                "Content-Type": "application/json"
            }
    
            data = {
                "email": settings.ESKIZ_EMAIL,
                "password": settings.ESKIZ_KEY
            }
            
            url = requests.post("https://notify.eskiz.uz/api/auth/login", data=json.dumps(data), headers=headers)
            
            if url.status_code == 200:
                response_data = url.json()
                token = response_data.pop("data").get("token")
                cache.set('cache_sms', token, 30*24*60*60)
            return token
        return token
    except:
        return None
    

def get_user_data():
    try:
        token = get_access_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token)
        }
        url = requests.get("https://notify.eskiz.uz/api/auth/user", headers=headers)
        
        if url.status_code == 200:
            response_data = url.json()
        return response_data
    except:
        return None