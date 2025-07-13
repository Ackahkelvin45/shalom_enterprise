from django.urls import path
from .views import index_view,Faq_view,about_view

app_name="main"

urlpatterns=[
    path("",view=index_view,name="index"),
    path("faq/",view=Faq_view,name="faq"),
    path("about/",view=about_view,name="about"),
]