import json
from django.contrib.auth import get_user_model
from djangochannelsrestframework import permissions
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
# from djangochannelsrestframework.consumers import AsyncAPIConsumer
from channels.db import database_sync_to_async
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.decorators import action
from djangochannelsrestframework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    PatchModelMixin,
    UpdateModelMixin,
    CreateModelMixin,
    DeleteModelMixin,
)
from .serializers import *
from .models import *


class LiveConsumer(	ListModelMixin,
					RetrieveModelMixin,
			    	PatchModelMixin,
			    	UpdateModelMixin,
			    	CreateModelMixin,
			    	DeleteModelMixin, GenericAsyncAPIConsumer):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "pk"

# ================================== Rooms and Messages in this Room ======================================
    async def disconnect(self, code):
        if hasattr(self, "room_subscribe"):
            await self.remove_user_from_room(self.room_subscribe)
            await self.notify_users()
        await super().disconnect(code)

# ================================== Manage Rooms ====================================
    @action()
    async def create_room(self, name, users, **kwargs):
        room, created = await Room.objects.async_get_or_create(
            host=self.scope["user"],
            name=name
        )
        users = await User.objects.async_filter(id__in=users)
        await database_sync_to_async(room.current_users.add)(*users)
        if not created:
        	return {"room": "is already exist"}, 404  # return the content and the response code.

#=========================== Plug message for each room ===============================
    @model_observer(Message, serializer_class=MessageSerializer)
    async def message_activity(self, message, action, subscribing_request_ids=[], **kwargs):
    	for request_id in subscribing_request_ids:
    		await self.reply(data=message, action=action, request_id=request_id)


    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f'room__{instance.room_id}'
        yield f'pk__{instance.pk}'

    @message_activity.groups_for_consumer
    def message_activity(self, room=None, **kwargs):
        if room is not None:
            yield f'room__{room}'


    @action()
    async def subscribe_to_messages_in_room(self, pk, request_id, **kwargs):
        await self.message_activity.subscribe(room=pk, request_id=request_id)

    @action()
    async def unsubscribe_to_messages_in_room(self, pk, request_id, **kwargs):
        await self.message_activity.unsubscribe(room=pk, request_id=request_id)
# ================================ custom actions for room and messages =======================================
    @action()
    async def join_room(self, pk, request_id, **kwargs):
    	if not await Room.objects.filter(pk=pk).async_exists():
    		return {"error": "room not found"}, 404  # return the content and the response code.
    	self.room_subscribe = pk
    	await self.add_user_to_room(pk)
    	await self.notify_users()
    	await self.subscribe_to_messages_in_room(pk, request_id, **kwargs)

    @action()
    async def leave_room(self, pk, request_id, **kwargs):
    	if not await Room.objects.filter(pk=pk, current_users=self.scope['user']).async_exists():
    		return {"error": "room not found"}, 404  # return the content and the response code.
    	await self.remove_user_from_room(pk)
    	await self.unsubscribe_to_messages_in_room(pk, request_id, **kwargs)

    @action()
    async def create_message(self, message, **kwargs):
        room: Room = await self.get_room(pk=self.room_subscribe)
        await database_sync_to_async(Message.objects.create)(
            room=room,
            user=self.scope["user"],
            text=message
        )


# ============================ Helper methods ====================================
    async def notify_users(self):
    	room: Room = await self.get_room(self.room_subscribe)
    	for group in self.groups:
    		await self.channel_layer.group_send(
                group,
                {
                    'type':'update_users',
                    'usuarios':await self.current_users(room)
                }
            )

    async def update_users(self, event: dict):
        await self.send(text_data=json.dumps({'usuarios': event["usuarios"]}))

    @database_sync_to_async
    def get_room(self, pk: int) -> Room:
        return Room.objects.get(pk=pk)

    @database_sync_to_async
    def current_users(self, room: Room):
        return [UserSerializer(user).data for user in room.current_users.all()]

    @database_sync_to_async
    def remove_user_from_room(self, room):
        user:User = self.scope["user"]
        user.current_rooms.remove(room)

    @database_sync_to_async
    def add_user_to_room(self, pk):
        user:User = self.scope["user"]
        if not user.current_rooms.filter(pk=self.room_subscribe).exists():
            user.current_rooms.add(Room.objects.get(pk=pk))

# ================================== Posts and Comments ===========================================

    # @model_observer(Comment, serializer_class=CommentSerializer)
    # async def comment_activity(self, message, action, subscribing_request_ids=[], **kwargs):
    # 	for request_id in subscribing_request_ids:
    # 		await self.reply(data=message, action=action, request_id=request_id)

    # @action()
    # async def subscribe_to_comment_activity(self, request_id, **kwargs):
    # 	await self.comment_activity.subscribe(request_id=request_id)
    	
    # @action()
    # async def unsubscribe_to_comment_activity(self, request_id, **kwargs):
    # 	await self.comment_activity.unsubscribe(request_id=request_id)


    # @action()
    # async def postcomment(self, request_id, data=None, **kwargs):
    # 	user = await User.objects.async_get(pk=data['user'])
    # 	await Comment.objects.async_create(text=data['text'], user=user)
    # 	return {}, 200  # return the content and the response code.
