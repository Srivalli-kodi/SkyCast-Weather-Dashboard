from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.index,
        name="home"
    ),

    path(
        "forecast/<str:city_name>/",
        views.forecast,
        name="forecast"
    ),

    path(
        "delete/<str:city_id>/",
        views.delete_city,
        name="delete_city"
    ),
]