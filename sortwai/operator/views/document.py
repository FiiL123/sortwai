from django.db.models import QuerySet
from django.urls import reverse
from django.views.generic import CreateView, ListView

from sortwai.waste.models import Document, Category
from sortwai.waste.views import get_active_municipality
from sortwai.waste.document import import_document, create_objects_from_document


class DocumentCreateView(CreateView):
    model = Document
    fields = ['name', 'text']
    template_name = 'document_form.html'
    success_url = 'operator:document_list'

    def get_success_url(self) -> str:
        return reverse('operator:document_list')

    def form_valid(self, form):
        municipality = get_active_municipality(self.request)
        if not municipality:
            raise ValueError("No active municipality found!")
        form.instance.municipality = municipality
        resp =  super().form_valid(form)
        upload = import_document(form.instance.id)
        create_objects_from_document(form.instance.name, municipality.id)
        return resp
class DocumentListView(ListView):
    model = Document
    template_name = 'document_list.html'

    def get_queryset(self) -> QuerySet[Document]:
        municipality = get_active_municipality(self.request)
        objects = Document.objects.filter(municipality=municipality).all()
        return objects