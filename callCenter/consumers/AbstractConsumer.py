import json

from asgiref.sync import async_to_sync

from callCenter.models import CallQueue, Customer


class AbstractConsumer:
    def send_call_queue_status(self):
        # Get the current call queue
        call_queue = CallQueue.all_pks()
        call_queue_list = []
        for call_pk in call_queue:
            call_queue_list.append(CallQueue.get(call_pk))
        # Send the updated call queue status to the group
        async_to_sync(self.channel_layer.group_send)(
            "call_queue",
            {
                'type': 'call_queue_status',
                'call_queue': [
                    {'customer_pk': call.customer_pk, 'customer_username': Customer.get(call.customer_pk).name, 'created_at': str(call.created_at)} for call in call_queue_list
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
        result_list = CallQueue.find(CallQueue.customer_pk == self.customer.pk).all()
        return result_list[0] if len(result_list) > 0 else None
