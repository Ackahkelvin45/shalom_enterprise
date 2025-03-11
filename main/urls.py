from django.urls import path
from .views import index_view

app_name="main"

urlpatterns=[
    path("",view=index_view,name="index")
]