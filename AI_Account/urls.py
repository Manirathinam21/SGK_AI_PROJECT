from django.urls import re_path
# from .views import homepage
# urlpatterns = [
# re_path('',homepage(r"/Users/praveen/Documents/Study/Projects/Aldi/Dried Herbs/mixed herbs.pdf"),name='Home Page' )]
# from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls import include, url
from django.views.static import serve
from django.shortcuts import render
from . import views
from django.urls import path, include , re_path


urlpatterns = [
    # re_path(r"home\/$", views.home, name='home'),
    re_path(r"ai\/$", views.ai_hub.as_view(), name='ai'),
 ]
