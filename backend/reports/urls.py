from django.urls import path

from . import views


urlpatterns = [
    path("analyze/", views.analyze, name="analyze"),
    path("store/", views.store, name="store"),
    path("history/", views.history, name="history"),
    path("report/<int:pk>/", views.report_detail, name="report-detail"),
]
