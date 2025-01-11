from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from sortwai.waste.models import BarCode, Category, Document, Location, Municipality


def get_active_municipality(request):
    if not hasattr(request, "_municipality"):
        request._municipality = Municipality.objects.first()

    return request._municipality


class CategoryListView(ListView):
    template_name = "categories.html"

    def get_queryset(self):
        return Category.objects.filter(
            municipality=get_active_municipality(self.request)
        ).select_related("target")


class DocumentListView(ListView):
    template_name = "docs.html"

    def get_queryset(self):
        return Document.objects.filter(
            municipality=get_active_municipality(self.request)
        )


class LocationListView(ListView):
    template_name = "locations.html"

    def get_queryset(self):
        return Location.objects.filter(
            municipality=get_active_municipality(self.request), show_on_main=True
        ).prefetch_related("targets")

    def get_context_data(self, *, object_list=..., **kwargs):
        ctx = super(LocationListView, self).get_context_data(**kwargs)
        ctx["map_pins"] = list(self.get_queryset().values_list("gps_lat", "gps_lon"))
        return ctx


class ScannerView(TemplateView):
    template_name = "scanner.html"


def get_trash(request, code):
    # item = get_object_or_404(BarCode, code=code)
    item = BarCode.objects.filter(code=code)
    if not item:
        return HttpResponse('<div id="qr-reader-results"><p>NOT FOUND</p></>')
    item = item.first()
    context = {"item": item}
    return render(request, "partials/product.html", context)
