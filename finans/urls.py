from django.urls import path

from . import views

urlpatterns = [
    path("mutabakatlar/", views.MutabakatlarView.as_view(), name="mutabakatlar"),
    path("kasalar/", views.KasalarView.as_view(), name="kasalar"),
]
