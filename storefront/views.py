# views.py
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

@api_view(['POST'])
def logout(request):
    try:
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return Response({'detail': 'Authorization header missing'}, status=status.HTTP_400_BAD_REQUEST)

        token = auth_header.split(' ')[1]  # Extract token from header
        refresh_token = RefreshToken(token)
        refresh_token.blacklist()
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
