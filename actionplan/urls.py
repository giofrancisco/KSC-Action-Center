from django.urls import path

from . import views


app_name = "actionplan"


urlpatterns = [
    path(
        "",
        views.problem_board,
        name="board",
    ),
    path(
        "lista/",
        views.problem_list,
        name="list",
    ),
    path(
        "<int:pk>/atualizar/",
        views.problem_update,
        name="update",
    ),
]
