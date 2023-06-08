import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from callCenter.consumers.AbstractConsumer import AbstractConsumer
from callCenter.models import Customer

WORKER_PERMISSION = "callCenter.view_customer"
class QueueConsumer(WebsocketConsumer, AbstractConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated or WORKER_PERMISSION not in self.user.get_user_permissions():
            self.close()
            return
        print("authenticated worker:", self.user.username)
        # Join the room group
        async_to_sync(self.channel_layer.group_add)("call_queue", self.channel_name)
        self.send_call_queue_status()
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
        async_to_sync(self.channel_layer.group_discard)(
            "call_queue",
            self.channel_name
        )

    def get_customer_by_customer_pk(self):
        # Check if the caller is the next in queue
        return Customer.get(self.customer_pk)



