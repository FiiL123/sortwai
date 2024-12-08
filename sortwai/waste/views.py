from django.views.generic import ListView
from sortwai.waste.models import Category, Municipality


def get_active_municipality(request):
    if not hasattr(request, "_municipality"):
        request._municipality = Municipality.objects.first()

    return request._municipality


class CategoryListView(ListView):
    template_name = "categories.html"

    def get_queryset(self):
        return Category.objects.filter(municipality=get_active_municipality(self.request))
