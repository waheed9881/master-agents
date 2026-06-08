import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class InboxConsumer(AsyncWebsocketConsumer):
    """Real-time inbox updates per tenant."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        tenant = getattr(user, "tenant", None)
        if not tenant:
            await self.close()
            return

        self.tenant_id = tenant.pk
        self.room_group_name = f"inbox_{self.tenant_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        # Client can ping for keepalive
        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def inbox_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "conversation_id": event["conversation_id"],
            "message": event["message"],
        }))
