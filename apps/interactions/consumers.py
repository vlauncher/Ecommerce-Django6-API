from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.shops.models import ShopMembership
from apps.shops.selectors import aget_shop_by_slug, aget_membership


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(code=4401)
            return
        shop = await aget_shop_by_slug(self.scope["url_route"]["kwargs"]["shop_slug"])
        membership = await aget_membership(shop, user) if shop else None
        conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        from .models import Conversation
        conversation = await Conversation.objects.aget(pk=conversation_id, shop=shop)
        if not membership or not membership.is_active or user.id not in {conversation.buyer_id, conversation.seller_id}:
            await self.close(code=4403)
            return
        self.room_group_name = f"conversation_{conversation_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "message" or not content.get("body"):
            return
        await self.channel_layer.group_send(self.room_group_name, {"type": "chat.message", "body": content["body"], "sender_id": self.scope["user"].id})

    async def chat_message(self, event):
        await self.send_json({"type": "message", "body": event["body"], "sender_id": event["sender_id"]})
