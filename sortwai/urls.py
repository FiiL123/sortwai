"""
URL configuration for sortwai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from sortwai.waste.views import (
    CategoryListView,
    ChatWidgetView,
    DocumentListView,
    ImageFormView,
    LocationListView,
    ScannerView,
    change_location,
    get_city,
    handle_scan,
    query_request,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", CategoryListView.as_view(), name="category_list"),
    path("docs/", DocumentListView.as_view(), name="document_list"),
    path("locations/", LocationListView.as_view(), name="location_list"),
    path("scanner/", ScannerView.as_view(), name="scanner"),
    path("image/", ImageFormView.as_view(), name="image"),
    path("scanner/<str:code>", handle_scan, name="scanner_product"),
    path("get_location/", get_city, name="get_city"),
    path("change_municipality/", change_location, name="change_municipality"),
    path("query_request/", query_request, name="query_request"),
    path("chat/", ChatWidgetView.as_view(), name="chat_widget"),
    path("operator/", include("sortwai.operator.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
