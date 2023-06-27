import json

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from rest_framework.views import APIView

from callCenter.serializers import CustomTokenObtainPairSerializer

import requests


class HomePageView(APIView):
    """
    API endpoint that allows authenticated users to view Home Page
    """

    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        self.push_notification_via_topic()
        return Response({"status": "notification pushed"}, status=status.HTTP_200_OK)

    def push_notification_via_topic(self, ):
        # Set headers
        headers = {
            'Authorization': 'key=AAAAvKGU00w:APA91bFtidUTFDZ6ML68xstSeICdixfUvkjn9TmRHbTbkPC7LAzgHDx73LCaUM_ZqmCrTqfNizY3P5ee95P9KhGmqFvJht_WTqp0XI1hecu_fzC3Pxobjuw6sPLwHhvtqrZVlftrbiHX',
            'Content-Type': 'application/json',
            'Sender': 'id = 4258'
        }

        data = {
            "to": "/topics/22",
            "priority": "high",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "notification": {
                "title": "test 2",
                "body": "test 2",
                "sound": "default",
                "image": ""
            },
            "data": {
                "image": "",
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            }
        }

        # Convert data to JSON format
        json_data = json.dumps(data)

        # Send GET request with headers
        response = requests.post('https://fcm.googleapis.com/fcm/send', headers=headers, data=json_data)

        # Check the response
        print(response.content)


# Create your views here.
class TokenView(APIView):
    """
    API endpoint that allows creation of JWT for authorised users.
    """

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        authentication = JWTAuthentication()

        try:
            serializer.is_valid(raise_exception=True)
            validated_token = authentication.get_validated_token(serializer.validated_data['access'])
            user = authentication.get_user(validated_token)

            result = {"user_id": user.id, "groups": list(user.groups.values_list('name', flat=True)),
                      "permissions": user.get_user_permissions(), "token_info": serializer.validated_data}
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(result, status=status.HTTP_200_OK)
