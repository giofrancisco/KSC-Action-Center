from django.contrib import admin

from django.contrib.auth import views as auth_views

from django.urls import (
    include,
    path,
)


urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),


    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name=
            "registration/login.html"
        ),
        name="login",
    ),


    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),


    path(
        "endpoints/",
        include(
            "inventory.urls"
        ),
    ),


    path(
        "problemas/",
        include(
            (
                "actionplan.urls",
                "actionplan",
            ),
            namespace=
            "actionplan",
        ),
    ),


    path(
        "wsus/",
        include(
            "wsus.urls"
        ),
    ),


    path(
        "",
        include(
            "dashboard.urls"
        ),
    ),

]