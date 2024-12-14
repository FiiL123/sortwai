from django.views.generic import ListView
from sortwai.waste.models import Category, Municipality, Document, Location


def get_active_municipality(request):
    if not hasattr(request, "_municipality"):
        request._municipality = Municipality.objects.first()

    return request._municipality


class CategoryListView(ListView):
    template_name = "categories.html"

    def get_queryset(self):
        return Category.objects.filter(municipality=get_active_municipality(self.request)).select_related("target")


class DocumentListView(ListView):
    template_name = "docs.html"

    def get_queryset(self):
        return Document.objects.filter(municipality=get_active_municipality(self.request))


class LocationListView(ListView):
    template_name = "locations.html"

    def get_queryset(self):
        return Location.objects.filter(municipality=get_active_municipality(self.request), show_on_main=True).prefetch_related("targets")

    def get_context_data(self, *, object_list = ..., **kwargs):
        ctx = super(LocationListView, self).get_context_data(**kwargs)
        ctx["map_pins"] = list(self.get_queryset().values_list("gps_lat", "gps_lon"))
        return ctx
