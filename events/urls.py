from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule/', views.schedule, name='schedule'),
    path('news/', views.news, name='news'),
    path('results/', views.results, name='results'),
    path('results/<int:result_id>/', views.result_detail, name='result_detail'),
    path('points/', views.points_table, name='points'),
    path('chat/', views.chat_with_gpt, name='chat'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)