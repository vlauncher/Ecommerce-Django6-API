from django.contrib import admin

from .models import Conversation, Dispute, Message, Notification, Offer, Review

for model in (Conversation, Dispute, Message, Notification, Offer, Review):
    admin.site.register(model)
