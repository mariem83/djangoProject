import json
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from callCenter.models import Customer, NotificationChannel

WORKER_PERMISSION = "callCenter.view_customer"


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            self.close()
            return
        print("authenticated user:", self.user.username)
        # Join the room group
        self.notification_channel = self.get_notification_channel_by_user_id()
        async_to_sync(self.channel_layer.group_add)(self.notification_channel.pk, self.channel_name)
        self.accept()

    def receive(self, text_data):
        print('in receive method')
        # Handle incoming WebSocket messages
        data = json.loads(text_data)
        print("received Data: ", data)
        message_type = data.get('type')
        if message_type == 'choose_call':
            self.customer_pk = data.get('room')
            self.customer = self.get_customer_by_customer_pk()
            if self.customer:
                self.call_queue = self.get_call_queue_by_customer()
                if self.call_queue:
                    self.call_queue.delete()
                    self.send_call_queue_status()
                    return
        print("error in updating the queue or in sending the event")

    def disconnect(self, close_code):
        print('in disconnect method')
        # Perform any necessary cleanup tasks when a WebSocket connection is closed
        if hasattr(self,'notification_channel') and self.notification_channel:
            async_to_sync(self.channel_layer.group_discard)(
                self.notification_channel.pk,
                self.channel_name
            )

    def get_notification_channel_by_user_id(self):
        # Check if the caller is the next in queue
        result_list = NotificationChannel.find(NotificationChannel.user_id == self.user.id).all()
        if len(result_list) > 0:
            return result_list[0]
        else:
            return NotificationChannel(user_id=self.user.id, created_at=datetime.now())
