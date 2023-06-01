import json

from asgiref.sync import async_to_sync

from callCenter.models import CallQueue


class AbstractConsumer:
    def send_call_queue_status(self):
        # Get the current call queue
        call_queue = CallQueue.objects.all()
        # Send the updated call queue status to the group
        async_to_sync(self.channel_layer.group_send)(
            "call_queue",
            {
                'type': 'call_queue_status',
                'call_queue': [
                    {'customer_username': call.customer.name} for call in call_queue
                ],
            }
        )

    def call_queue_status(self, event):
        # Send the call queue status to the consumer
        self.send(text_data=json.dumps({
            'type': 'call_queue_status',
            'call_queue': event['call_queue'],
        }))

    def get_call_queue_by_customer(self):
        try:
            return CallQueue.objects.get(customer=self.customer)
        except CallQueue.DoesNotExist:
            return None
