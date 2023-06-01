from django.db import models

from django.conf import settings


# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=200, blank=True, null=True)
    # Add any additional fields or methods as per your requirements


class Worker(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=200, blank=True, null=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    # Add any additional fields or methods as per your requirements


class ChatRoom(models.Model):
    customer = models.OneToOneField('callCenter.Customer', on_delete=models.CASCADE)
    worker = models.ForeignKey('callCenter.Worker', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Add any additional fields or methods as per your requirements


class ChatMessage(models.Model):
    room = models.ForeignKey('callCenter.ChatRoom', on_delete=models.CASCADE)
    content = models.CharField(max_length=100)
    sender_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class CallQueue(models.Model):
    customer = models.ForeignKey('callCenter.Customer', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Add any additional fields or methods as per your requirements
