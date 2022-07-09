from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone



User = get_user_model()


class Room(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    current_users = models.ManyToManyField(User, related_name="current_rooms", blank=True)

    def __str__(self):
        return f"Room({self.name} {self.host})"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message({self.user} {self.room})"


class Post(models.Model):
    # relation
    room    		= models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_post')
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_post')
    # attrs
    content         = models.TextField()
    # likes           = models.IntegerField(default=0)
    created_at      = models.DateTimeField('date created', default=timezone.now)

    def __str__(self):
        return f"Post({self.content} {self.room})"

        
class Comment(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comment')
    post            = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comment')
    # attrs
    content         = models.TextField()
    created_at      = models.DateTimeField('date created', default=timezone.now)
    
    def __str__(self):
        return f"Comment({self.user.username} {self.content})"

