from django.contrib import admin
from django.urls import path, include


GLOBAL_TOKEN = "PROD1"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("oauth/", include("allauth.urls")),
    path("api/", include("api.urls")),
    path("", include("home.urls")),
]
