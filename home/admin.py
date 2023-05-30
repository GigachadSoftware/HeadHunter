from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import User, Vacancy

admin.site.register(User)
admin.site.register(Vacancy)
admin.site.register(Session)
