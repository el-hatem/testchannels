from .consumers import LiveConsumer
from django.urls import  re_path
websocket_urlpatterns = [
    re_path(r'^ws/$', LiveConsumer.as_asgi()),
]