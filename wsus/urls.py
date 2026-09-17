from django.urls import path

from . import views


app_name = "wsus"


urlpatterns = [

    path(
        "computadores/",
        views.computer_list,
        name="computers",
    ),

    path(
        "atividades/",
        views.activity_board,
        name="activities",
    ),

]