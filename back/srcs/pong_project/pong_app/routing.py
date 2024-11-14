#This file defines routes for WebSockets, similar to how urls.py handles HTTP routes in Django. 
#The re_path function is like path, but allows regular expressions to define more complex paths.
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/pong-socket/(?P<userid>\d+)/(?P<userid2>\d+)/$', consumers.PongConsumer.as_asgi()), 
    re_path(r'ws/pong-socket/(?P<tournament>\w+)/(?P<userid>\d+)/$', consumers.TournamentConsumer.as_asgi()), 
    # 'w+' sirve para crear nuevas rooms por cada llamada mientras que el 
    # '$' sirve para indicar que ahí se acaba la url, si añades algo después no lo va a encontrar
]
