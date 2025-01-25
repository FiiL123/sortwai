from django.db.models import QuerySet
from django.views.generic import ListView

from sortwai.waste.models import Category
from sortwai.waste.views import get_active_municipality


class CategoryListView(ListView):
    model = Category
    template_name = 'category_list.html'

    def get_queryset(self) -> QuerySet[Category]:
        municipality = get_active_municipality(self.request)
        objects = Category.objects.filter(municipality=municipality).all()
        return objects