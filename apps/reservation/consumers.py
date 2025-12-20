import json
from apps.core.utils import json_datetime_serializer

from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import filter_reservation


class ReservationConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user is None:
            await self.close()
        else:
            username = self.user.username
            self.room_group_name = f"reservation_{username}"
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
            "list_reservation": self.validate_list,
            
        }
        await available_methods[event_type]()
    

    async def validate_list(self):
        reservation_query = await filter_reservation()
        await self.channel_layer.group_send(self.room_group_name, {"type": "list_reservation",
                                                                   "reservation_query": reservation_query})
        
    async def new_reservation(self, event):
        message = dict(event)
        await self.send(text_data=json.dumps(message))


    async def list_reservation(self, event):
        await self.send(text_data=json.dumps(event, default=json_datetime_serializer, ensure_ascii=False))
        
        
    async def edit_reservation(self, event):
        message = dict(event)
        await self.send(text_data=json.dumps(message))