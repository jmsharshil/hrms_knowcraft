from django.urls import path,include
from .views import support_bot
urlpatterns = [
    path('support/',support_bot,name='support')
]