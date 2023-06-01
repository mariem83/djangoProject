from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import urllib.parse

from django.db import transaction
from django.db.models import F

from callCenter.consumers.AbstractConsumer import AbstractConsumer
from callCenter.models import ChatRoom, Customer, ChatMessage, Worker, CallQueue


class CallerConsumer(WebsocketConsumer, AbstractConsumer):

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            self.close()
            return

        print("authenticated customer:", self.user.username)

        if "callCenter.view_caller" not in self.get_user_permissions():
            self.establish_customer_connection()
        else:
            self.establish_worker_connection()
        self.accept()

    def receive(self, text_data):

        # Handle incoming WebSocket messages
        data = json.loads(text_data)
        print("received Data: ", data)
        message_type = data.get('type')
        if message_type == 'chat_message':
            content = data.get('content')
            chat_message = ChatMessage(room=self.chat_room, content=content, sender_name=self.user.username)
            self.create_chat_message(chat_message)
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message_pub',
                    'message': self.user.username + ": " + content,
                }
            )

    def disconnect(self, close_code):
        # Perform any necessary cleanup tasks when a WebSocket connection is closed
        print('in disconnect method')

        if close_code == 3111:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
        elif "callCenter.view_caller" in self.get_user_permissions() or close_code == 3013:
            self.clear_chat_history()
            self.close_call()
        elif close_code == 3012:
            self.call_queue = self.get_call_queue_by_customer()
            if self.call_queue:
                self.call_queue.delete()
                self.send_call_queue_status()
            self.clear_chat_history()
            self.close_call()

        else:
            if hasattr(self, 'room_group_name'):
                async_to_sync(self.channel_layer.group_discard)(
                    self.room_group_name,
                    self.channel_name
                )

    @transaction.atomic
    def establish_customer_connection(self):
        self.close_code = 3012
        self.customer = self.get_customer()
        if not self.customer:
            self.customer = Customer(user=self.user, name=self.user.username, email=self.user.email)
            self.create_customer()
        self.chat_room = self.get_chat_room_by_customer()
        if not self.chat_room:
            self.chat_room = ChatRoom(customer=self.customer)
            self.create_chat_room()
            self.add_call_to_queue()
            self.send_call_queue_status()
        self.room_group_name = 'call_%s' % self.user.username
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name)
        self.send_chat_messages()

    @transaction.atomic
    def establish_worker_connection(self):
        self.close_code = 3013
        self.worker = self.get_worker()
        if not self.worker:
            self.worker = Worker(user=self.user, name=self.user.username, email=self.user.email)
            self.create_worker()
        params = urllib.parse.parse_qs(self.scope['query_string'].decode('utf8'))
        self.customer_username = params.get('room', ('Not Supplied',))[0]
        if self.customer_username != "Not Supplied":
            self.customer = self.get_customer_by_username()
            if self.customer:
                self.chat_room = self.get_chat_room_by_customer()
                if self.chat_room:
                    self.update_chat_room_with_worker()
                    self.room_group_name = 'call_%s' % self.chat_room.customer.name
                    async_to_sync(self.channel_layer.group_add)(
                        self.room_group_name,
                        self.channel_name)
                    self.send_chat_messages()
                    self.call = self.get_call_from_queue()
                    if self.call:
                        self.delete_call_from_queue()
                    self.send_call_queue_status()
                    return
        self.close(1007)

    def create_chat_room(self):
        # Create a chat room with the chosen caller
        self.chat_room.save()

    def create_customer(self):
        # Create a chat room with the chosen caller
        self.customer.save()

    def create_worker(self):
        # Create a chat room with the chosen caller
        self.worker.save()

    def create_chat_message(self, chat_message):
        # Create a chat room with the chosen caller
        chat_message.save()

    def get_user_permissions(self):
        return self.user.get_user_permissions()

    def get_customer(self):
        # Check if the caller is the next in queue
        try:
            return Customer.objects.get(user=self.user)
        except Customer.DoesNotExist:
            return None

    def get_customer_by_username(self):
        # Check if the caller is the next in queue
        try:
            return Customer.objects.get(name=self.customer_username)
        except Customer.DoesNotExist:
            return None

    def get_worker(self):
        # Check if the caller is the next in queue
        try:
            return Worker.objects.get(user=self.user)
        except Worker.DoesNotExist:
            return None

    def get_chat_room_by_customer(self):
        try:
            return ChatRoom.objects.get(customer=self.customer)
        except ChatRoom.DoesNotExist:
            return None

    def add_call_to_queue(self):
        # Add the caller to the call queue
        CallQueue.objects.create(customer=self.customer)

    def get_chat_room_by_worker(self):
        try:
            return ChatRoom.objects.get(worker=self.worker)
        except ChatRoom.DoesNotExist:
            return None

    def update_chat_room_with_worker(self):
        self.chat_room.worker = self.worker
        self.chat_room.save()

    def send_chat_messages(self):
        messages = self.get_chat_messages_ordered_by_timestamp()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_status',
                'messages': [
                    {'content': message.content,
                     'sender': message.sender_name,
                     'created_at': str(message.created_at)} for message in messages
                ],
            }
        )

    def chat_status(self, event):
        message = event["messages"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"close_code": self.close_code, "messages": message}))

    def chat_message_pub(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))

    def get_call_from_queue(self):
        try:
            return CallQueue.objects.get(customer=self.customer)
        except ChatRoom.DoesNotExist:
            return None

    def delete_call_from_queue(self):
        self.call.delete()

    def get_chat_messages_ordered_by_timestamp(self):
        objects = ChatMessage.objects.filter(room=self.chat_room).order_by(F('created_at').asc()).all()
        return objects

    def clear_chat_history(self):
        self.chat_room.delete()

    def close_call(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'close_call_all',
                'code': self.close_code
            }
        )

    def close_call_all(self, event):
        self.close(3111)
