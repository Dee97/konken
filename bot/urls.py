from django.urls import path
from bot import views
urlpatterns = [
    path('callback/<str:short_name>/', views.callback_new, name = "bot-callback" ),
    # path('callback/', views.callback, name="callback"),
    path('refresh-menu/', views.RefreshRichMenu.as_view(), name='refresh-menu'),
]