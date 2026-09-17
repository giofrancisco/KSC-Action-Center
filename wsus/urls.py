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

    path(
        "computador/<int:computer_id>/atividade/criar/",
        views.task_create,
        name="task_create",
    ),

    path(
        "atividade/<int:pk>/atualizar/",
        views.task_update,
        name="task_update",
    ),

    path(
        "atividade/<int:pk>/historico/",
        views.task_history,
        name="task_history",
    ),

]
