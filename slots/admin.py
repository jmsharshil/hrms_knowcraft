from django.contrib import admin
from .models import Slot,Interviewer,InterviewFeedback,InterviewLocation
# Register your models here.

admin.site.register(Slot)
admin.site.register(Interviewer)
admin.site.register(InterviewFeedback)
admin.site.register(InterviewLocation)