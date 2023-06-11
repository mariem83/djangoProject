from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import urllib.parse

from datetime import datetime

from redis_om import NotFoundError

from callCenter.consumers.AbstractConsumer import AbstractConsumer
from callCenter.models import ChatRoom, Customer, ChatMessage, Worker, CallQueue

WORKER_PERMISSION = "callCenter.view_customer"
CHAT_TTL = 5400


class CallerConsumer(WebsocketConsumer, AbstractConsumer):

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            self.close()
            return

        print("authenticated customer:", self.user.username)

        if WORKER_PERMISSION not in self.get_user_permissions():
            self.establish_customer_connection()
        else:
            self.establish_worker_connection()
        self.accept()

    def receive(self, text_data):

        # Handle incoming WebSocket messages
        data = json.loads(text_data)
        print("received Data: ", data)
        message_type = data.get('type')
        if message_type:
            if message_type == 'chat_message':
                content = data.get('content')
                chat_message = ChatMessage(room_pk=self.chat_room.pk, content=content, sender_name=self.user.username,
                                           created_at=datetime.now())
                self.create_chat_message(chat_message)
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message_pub',
                        'message': self.user.username + ": " + content,
                        'created_at': chat_message.pk
                    }
                )

    def disconnect(self, close_code):
        # Perform any necessary cleanup tasks when a WebSocket connection is closed
        print('in disconnect method')

        if close_code == 3111:
            if hasattr(self, 'room_group_name'):
                async_to_sync(self.channel_layer.group_discard)(
                    self.room_group_name,
                    self.channel_name
                )
        elif WORKER_PERMISSION in self.get_user_permissions() or close_code == 3013:
            self.clear_chat_history()
            self.close_call()
        elif close_code == 3012:
            self.call_queue = self.get_call_queue_by_customer()
            if self.call_queue:
                self.call_queue.delete(pk=self.call_queue.pk)
                self.send_call_queue_status()
            self.clear_chat_history()
            self.close_call()

        else:
            if hasattr(self, 'room_group_name'):
                async_to_sync(self.channel_layer.group_discard)(
                    self.room_group_name,
                    self.channel_name
                )
        if self.customer:
            self.chat_room = self.get_chat_room_by_customer()
            if self.chat_room:
                if not Worker.get(self.chat_room.worker_pk):
                    self.clear_chat_history()
                    if self.call_queue:
                        self.call_queue.delete(pk=self.call_queue.pk)
                        self.send_call_queue_status()

    def establish_customer_connection(self):
        self.close_code = 3012
        self.customer = self.get_customer()
        if not self.customer:
            self.customer = Customer(user_id=self.user.id, name=self.user.username, email=self.user.email)
            self.create_customer()
        self.chat_room = self.get_chat_room_by_customer()
        if not self.chat_room:
            self.chat_room = ChatRoom(customer_pk=self.customer.pk, created_at=datetime.now())
            self.create_chat_room()
            self.add_call_to_queue()
            self.send_call_queue_status()
        self.room_group_name = 'call_%s' % self.customer.pk
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name)
        self.send_chat_messages()

    def establish_worker_connection(self):
        self.close_code = 3013
        self.worker = self.get_worker()
        if not self.worker:
            self.worker = Worker(user_id=self.user.id, name=self.user.username, email=self.user.email)
            self.create_worker()
        params = urllib.parse.parse_qs(self.scope['query_string'].decode('utf8'))
        self.customer_pk = params.get('room', ('Not Supplied',))[0]
        if self.customer_pk != "Not Supplied":
            self.customer = self.get_customer_by_customer_pk()
            if self.customer:
                self.chat_room = self.get_chat_room_by_customer()
                if self.chat_room:
                    self.update_chat_room_with_worker()
                    self.room_group_name = 'call_%s' % self.chat_room.customer_pk
                    async_to_sync(self.channel_layer.group_add)(
                        self.room_group_name,
                        self.channel_name)
                    self.send_chat_messages()
                    self.call = self.get_call_from_queue()
                    if self.call:
                        self.delete_call_from_queue()
                    self.send_call_queue_status()
                    return
        self.close(code=3111)

    def create_chat_room(self):
        # Create a chat room with the chosen caller
        self.chat_room.save()
        # Expire the model after 24 hrs (86400 seconds)
        self.chat_room.expire(CHAT_TTL)

    def create_customer(self):
        # Create a chat room with the chosen caller
        self.customer.save()
        self.customer.expire(CHAT_TTL)

    def create_worker(self):
        # Create a chat room with the chosen caller
        self.worker.save()
        self.worker.expire(CHAT_TTL)

    def create_chat_message(self, chat_message):
        # Create a chat room with the chosen caller
        chat_message.save()
        chat_message.expire(CHAT_TTL)

    def get_user_permissions(self):
        return self.user.get_user_permissions()

    def get_customer(self):
        # Check if the caller is the next in queue
        result_list = Customer.find(Customer.user_id == self.user.id).all()
        return result_list[0] if len(result_list) > 0 else None

    def get_customer_by_customer_pk(self):
        # Check if the caller is the next in queue
        try:
            return Customer.get(self.customer_pk)
        except NotFoundError:
            return None

    def get_worker(self):
        # Check if the caller is the next in queue
        result_list = Worker.find(Worker.user_id == self.user.id).all()
        return result_list[0] if len(result_list) > 0 else None

    def get_chat_room_by_customer(self):
        result_list = ChatRoom.find(ChatRoom.customer_pk == self.customer.pk).all()
        return result_list[0] if len(result_list) > 0 else None

    def add_call_to_queue(self):
        # Add the caller to the call queue
        self.call_queue = CallQueue(customer_pk=self.customer.pk, created_at=datetime.now())
        self.call_queue.save()
        self.call_queue.expire(CHAT_TTL)

    def get_chat_room_by_worker(self):
        result_list = ChatRoom.find(ChatRoom.worker_pk == self.worker.pk).all()
        return result_list[0] if len(result_list) > 0 else None

    def update_chat_room_with_worker(self):
        self.chat_room.worker_pk = self.worker.pk
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
        result_list = CallQueue.find(CallQueue.customer_pk == self.customer.pk).all()
        return result_list[0] if len(result_list) > 0 else None

    def delete_call_from_queue(self):
        self.call.delete(pk=self.call.pk)

    def get_chat_messages_ordered_by_timestamp(self):
        objects = ChatMessage.find(ChatMessage.room_pk == self.chat_room.pk).all()
        return objects

    def clear_chat_history(self):
        if hasattr(self, 'chat_room') and self.chat_room:
            self.chat_room.delete(pk=self.chat_room.pk)
            messages = ChatMessage.find(ChatMessage.room_pk == self.chat_room.pk).all()
            for message in messages:
                message.delete(pk=message.pk)

    def close_call(self):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'close_call_all',
                    'code': self.close_code
                }
            )

    def close_call_all(self, event):
        self.close(3111)
