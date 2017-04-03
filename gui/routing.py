from channels.routing import route
from .views import ws_message
channel_routing = [
    route("websocket.receive", ws_message),
]
