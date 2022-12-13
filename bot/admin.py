from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import FakeName

admin.site.register(FakeName)
