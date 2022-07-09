import random
import re
from django.contrib.auth import authenticate
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.response import Response
from django.db.models import Q
from .serializers import *
from django.conf import settings
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

# ############# Main App ##############
from .models import *
from .serializers import *
#=================================
# Create your views here.


# Register API
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

def get_client_ip(request):
    ip = request.META.get('HTTP_X_REAL_IP')
    return ip

@api_view(['POST'])
@csrf_exempt
@permission_classes((AllowAny,))
def register_view(request):
    data = {}
    if 'first_name' and 'last_name' and 'username' and 'email' \
        and 'phone' and 'gender' and 'password' in request.data:

        username=request.data['username']
        # request.data['username']=username
        email=request.data['email']
        userfilter =UserInfo.objects.filter(username=username)
        emailfilter = UserInfo.objects.filter(email=email)
        if userfilter.exists():
            username=f"{username}_{str(random.randint(1,9999))}"

        elif emailfilter.exists():
            data['error'] = 'email Exist Before!'
            return Response(data)
        elif checkEmail(email)==False:
            data['error'] = 'Not Valid Email'
            return Response(data)

        serializer=RegiterationrSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()
            data['response']='Sign-Up Sussefuly'
            data['UserPhoto']='media/UsersPhoto/defult.png'
            data['email']=user.email
            data['username']=user.username
            data['token']=Token.objects.get(user=user).key
        else:
            data=serializer.errors
    else:
        data['error'] = 'missing values'
    return Response(data)
