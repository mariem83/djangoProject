from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from rest_framework.views import APIView

from callCenter.serializers import CustomTokenObtainPairSerializer


class HomePageView(APIView):
    """
    API endpoint that allows authenticated users to view Home Page
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"status": "authenticated_request"}, status=status.HTTP_200_OK)

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
