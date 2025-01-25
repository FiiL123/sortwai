from django.db.models import QuerySet
from django.urls import reverse
from django.views.generic import CreateView, ListView

from sortwai.waste.models import Document, Category
from sortwai.waste.views import get_active_municipality


class DocumentCreateView(CreateView):
    model = Document
    fields = ['name', 'file']
    template_name = 'document_form.html'
    success_url = 'operator:document_list'

    def get_success_url(self) -> str:
        return reverse('operator:document_list')

    def form_valid(self, form):
        municipality = get_active_municipality(self.request)
        if not municipality:
            raise ValueError("No active municipality found!")
        form.instance.municipality = municipality
        return super().form_valid(form)
class DocumentListView(ListView):
    model = Document
    template_name = 'document_list.html'

    def get_queryset(self) -> QuerySet[Document]:
        municipality = get_active_municipality(self.request)
        objects = Document.objects.filter(municipality=municipality).all()
        return objects