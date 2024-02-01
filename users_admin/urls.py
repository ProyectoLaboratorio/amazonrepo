"""users_admin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from user_profile_api.views import activate_audio, video, show_doors, show_doors_devices, video_open_door, show_users_devices, show_users, get_users, show_events, show_events_devices, GetEventsView, GetDoorsView, schedule_career, schedule_career_home, schedule_career_home_year
urlpatterns = [
    path('video/open_door/<str:device>/', video_open_door, name='video_open_door'),
    path('show_users/<str:device>/get_users/', get_users, name='get_users'),
    path('show_events/<str:device>/get_events/', GetEventsView.as_view(), name='get_events'),
    path('show_doors/<str:device>/show_doors/', GetDoorsView.as_view(), name='get_doors'),

    path('horario/<str:career>/<str:year>', schedule_career, name='schedule_career'),
    path('horario/<str:career>/', schedule_career_home_year, name='schedule_career_home_year'),
    path('horario/', schedule_career_home, name='schedule_career_home'),
    path('video/', video, name='video'),
    path('audio/activate/<str:device>/', activate_audio, name='activate_audio'),
    path('show_users/<str:device>/', show_users, name='show_users'),
    path('show_users/', show_users_devices, name='show_users_devices'),
    path('show_events/<str:device>/', show_events, name='show_events'),
    path('show_events/', show_events_devices, name='show_events_devices'),
    path('show_doors/<str:device>/', show_doors, name='show_doors'),
    path('show_doors/', show_doors_devices, name='show_doors_devices'),
    path('', admin.site.urls)
]
