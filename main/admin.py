from django.contrib import admin
from .models import Campaign, Application, UserProfile, Content 
from . models import Plan

# Register your models here.
admin.site.register(Campaign)
admin.site.register(Application)
admin.site.register(UserProfile)
admin.site.register(Content) 
admin.site.register(Plan) 