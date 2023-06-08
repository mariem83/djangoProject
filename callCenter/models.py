import datetime
from typing import Optional
from redis_om import (
    Field,
    HashModel,
    Migrator
)
from redis_om import get_redis_connection

# Create your models here.

class Customer(HashModel):
    user_id : int = Field(index=True)
    name : str = Field(index=True)
    email : str
    # Add any additional fields or methods as per your requirements


class Worker(HashModel):
    name : str = Field(index=True)
    email : str
    user_id : int = Field(index=True)
    # Add any additional fields or methods as per your requirements


class ChatRoom(HashModel):
    customer_pk : str = Field(index=True)
    worker_pk : Optional[str] = Field(index=True)
    created_at : datetime.datetime

    # Add any additional fields or methods as per your requirements


class ChatMessage(HashModel):
    room_pk : str = Field(index=True)
    content : str
    sender_name : str
    created_at : datetime.datetime


class CallQueue(HashModel):
    customer_pk : str = Field(index=True)
    created_at : datetime.datetime

redis = get_redis_connection()
Migrator().run()