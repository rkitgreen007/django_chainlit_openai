# myproject/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.site),
    # Serve a simple template hosting our Chainlit frame
    path('chat/', TemplateView.as_view(template_name="chat.html"), name="chat_page"),
]
