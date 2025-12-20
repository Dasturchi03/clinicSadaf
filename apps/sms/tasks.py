import requests
import json
from clinicSADAF.celery import celery_app
from psycopg2 import OperationalError
from apps.sms.utils import get_access_token


@celery_app.task(
    queue="send_sms",
    name="send_sms_with_code",
    autoretry_for=(OperationalError,)
    )
def send_sms_with_code(message: str, mobile_phone: str):
    
    try:
        token = get_access_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token)
        }
        
        data = {
            "message": message,
            "mobile_phone": mobile_phone[1:],
            "from": 4546
        }
        
        url = requests.post("https://notify.eskiz.uz/api/message/sms/send", data=json.dumps(data), headers=headers)
        
        if url.status_code == 200:
            response_data = url.json()
            return response_data
    except:
        return None