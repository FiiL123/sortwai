from sortwai.operator.views import document, category
from django.urls import path
app_name = 'operator'

urlpatterns = [
    path('document/', document.DocumentCreateView.as_view(), name='document_create'),
    path('documents/', document.DocumentListView.as_view(), name='document_list'),
    path('categories/', category.CategoryListView.as_view(), name='category_list'),
]