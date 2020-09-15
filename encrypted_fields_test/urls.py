"""encrypted_fields_test URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .views import DemoListView, DemoCreateView, DemoUpdateView
from .api_views import DemoModelViewset

urlpatterns = [path("admin/", admin.site.urls)]
urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
]
urlpatterns += [
    path("demomodel/", DemoListView.as_view(), name="demomodel-list"),
    path("demomodel/add/", DemoCreateView.as_view(), name="demomodel-add"),
    path("demomodel/<int:pk>/", DemoUpdateView.as_view(), name="demomodel-update"),
]
router = routers.DefaultRouter()
router.register(r"demomodel", DemoModelViewset, basename="api-demomodel")
urlpatterns += [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
