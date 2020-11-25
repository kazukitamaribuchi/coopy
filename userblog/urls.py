from django.urls import path
from . import userblog_views
from blog import views

app_name = 'userblog'

urlpatterns = [
    path('<slug>/', userblog_views.UserBlogView.as_view(), name='userblog'),
    path('<slug>/entry/<str:pk>/', userblog_views.PostDetailView.as_view(), name='post_detail'),
]
