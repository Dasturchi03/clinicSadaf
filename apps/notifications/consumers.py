import json
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.core.utils import json_datetime_serializer
from .utils import filter_notification

class NotificationConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user is None:
            await self.close()
        else:
            username = self.user.username
            self.room_group_name = f"notification_{username}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()


    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        await self.get_event(data["type"])
        
        
    async def get_event(self, event_type):
        available_methods: dict = {
            "list_notification": self.validate_list,
            
        }
        await available_methods[event_type]()
    

    async def validate_list(self):
        notification_query = await filter_notification(self.user.id)
        await self.channel_layer.group_send(self.room_group_name, {"type": "list_notification",
                                                                   "notification_query": notification_query})
        
    async def new_notification(self, event):
        message = dict(event)
        await self.send(text_data=json.dumps(message))


    async def list_notification(self, event):
        await self.send(text_data=json.dumps(event, default=json_datetime_serializer, ensure_ascii=False))
