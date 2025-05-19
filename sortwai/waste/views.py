import json
from unicodedata import category
from urllib.parse import urlparse

import requests

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, FormView
from django.urls import reverse

from geopy import Nominatim

from sortwai.settings import IMAGE_RECOGNITION_API
from sortwai.waste.forms import MunicipalityForm, ImageForm
from sortwai.waste.models import BarCode, Category, Document, Location, Municipality


def get_active_municipality(request) -> Municipality | None:
    if city := request.COOKIES.get("municipality"):
        municipality = Municipality.objects.filter(id=city)
        if municipality.exists():
            return municipality.first()

    return None


def active_municipality(request):
    if request.COOKIES.get("municipality"):
        return {"municipality": get_active_municipality(request)}
    else:
        return {"municipality": None}


class CategoryListView(ListView):
    template_name = "categories.html"

    def get_queryset(self):
        return Category.objects.filter(
            municipality=get_active_municipality(self.request)
        ).select_related("target")

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        municipality_form = MunicipalityForm()
        context["municipality_form"] = municipality_form
        if code := self.request.GET.get("q"):
            item = BarCode.objects.filter(code=code)
            if item:
                item = item.first()
                context.update({"item": item})
        return context


class DocumentListView(ListView):
    template_name = "docs.html"

    def get_queryset(self):
        return Document.objects.filter(
            municipality=get_active_municipality(self.request),

        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        municipality_form = MunicipalityForm()
        context["municipality_form"] = municipality_form
        return context


class LocationListView(ListView):
    template_name = "locations.html"

    def get_queryset(self):
        return Location.objects.filter(
            municipality=get_active_municipality(self.request), show_on_main=True
        ).prefetch_related("targets")

    def get_context_data(self, *, object_list=..., **kwargs):
        ctx = super(LocationListView, self).get_context_data(**kwargs)

        municipality_form = MunicipalityForm()
        ctx["municipality_form"] = municipality_form

        ctx["map_pins"] = list(self.get_queryset().values_list("gps_lat", "gps_lon"))
        return ctx


class ScannerView(TemplateView):
    template_name = "scanner.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_url'] = reverse('category_list')
        return context


def get_trash(request, code):
    # item = get_object_or_404(BarCode, code=code)
    item = BarCode.objects.filter(code=code)
    if not item:
        return HttpResponse('<div id="qr-reader-results"><p>NOT FOUND</p></>')
    item = item.first()
    context = {"item": item}
    return render(request, "partials/product.html", context)


@csrf_exempt
def get_city(request):
    if request.method == "POST":
        try:
            # Parse the request body for latitude and longitude
            data = json.loads(request.body)
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude is None or longitude is None:
                return JsonResponse(
                    {"error": "Invalid coordinates provided."}, status=400
                )

            # Initialize Nominatim geocoder
            geolocator = Nominatim(user_agent="django_app")
            location = geolocator.reverse((latitude, longitude), exactly_one=True)

            if location:
                # Extract city name from address details
                address = location.raw.get("address", {})
                city = address.get(
                    "city", address.get("town", address.get("village", "Unknown"))
                )
                municipality = Municipality.objects.filter(name=city)
                if municipality.exists():
                    response = JsonResponse({"city": city}, status=200)
                    response.set_cookie("municipality", str(municipality.first().id))
                    return response
                else:
                    return JsonResponse(
                        {"error": "Municipality not found."}, status=404
                    )
        except Exception:
            return JsonResponse({"error": "Invalid coordinates provided."})
    else:
        return JsonResponse({"error": "Method must be POST."}, status=400)


def change_location(request):
    if request.method == "POST":
        form = MunicipalityForm(request.POST)
        if form.is_valid():
            municipality = form.cleaned_data["municipality"]
            referer = request.META.get("HTTP_REFERER")
            if referer:
                referer_path = urlparse(referer).path

                allowed_paths = [
                    reverse("category_list"),
                    reverse("document_list"),
                    reverse("location_list"),
                ]
                if referer_path in allowed_paths:
                    response = redirect(referer_path)
                else:
                    # default
                    response = redirect("category_list")
            else:
                # default
                response = redirect("category_list")

            response.set_cookie("municipality", municipality)
            return response


# @csrf_exempt
# def query_request2(request):
#     if request.method == "POST":
#         print("request called")
#         print(request.POST)
#         user_query = request.POST.get("q")
#         city = get_active_municipality(request).name
#         print(user_query)
#         print(city)
#         # response = {"id": 5, "name": "Papierovy papier"}
#         # category = get_object_or_404(Category, id=response.get("id"))
#         # print(category)
#         # return TemplateResponse(request, template="partials/categories2.html", context={"object_list": [category]})
#
#         if not user_query or not city:
#             return HttpResponse("MISSING DATA")
#
#         try:
#             req = requests.post("http://api:6969", json={"city":{"name": city},
#                                                             "request": {"contents": user_query}
#                                                             })
#             response_text = req.json()
#             print("resp", response_text)
#             category = get_object_or_404(Category, id=response_text.get("id"))
#             print(category)
#             return TemplateResponse(request, template="partials/categories2.html", context={"object_list": [category]})
#         except requests.exceptions.RequestException as e:
#             return JsonResponse({"response": "Error connecting to the external service."})
#     return JsonResponse({"response" : "Invalid request."})


def query_request(request):
    if request.method == "POST":
        user_query = request.POST.get("q")
        city = request.POST.get("city")

        if not user_query or not city:
            return JsonResponse({"response": "Missing data!"}, status=400)
        try:
            req = requests.post("http://api:6969", json={"city": {"name": city},
                                                         "request": {"contents": user_query}
                                                         })
            response_text = req.json()
            print(response_text)
            category = get_object_or_404(Category, id=response_text["response"][0]["id"])

            def limit_lines_to_list(text, max_lines=5):
                lines = text.splitlines()
                if len(lines) > max_lines:
                    lines = lines[:max_lines] + ["..."]
                return lines

            limited_do = limit_lines_to_list(category.do or "")
            limited_dont = limit_lines_to_list(category.dont or "")

            category_data = {
                "name": category.name,
                "image": category.image.url if category.image else None,
                "do": limited_do,
                "dont": limited_dont,
                "description": category.description
            }
            return JsonResponse({"response": response_text["response"][0], "category": category_data})
        except requests.exceptions.RequestException as e:
            return JsonResponse({"response": "Error connecting to the external service."})
    return JsonResponse({"response": "Invalid request."})


class ImageFormView(FormView):
    template_name = "image.html"
    form_class = ImageForm
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_url'] = reverse('category_list')
        return context


    # def get(self, request, *args, **kwargs):
    #     return render(request, self.template_name, {"image_form": ImageForm()})

    def post(self, request, *args, **kwargs):
        image_form = self.form_class(request.POST, request.FILES)
        if image_form.is_valid():
            image = image_form.cleaned_data["image"]
            url = IMAGE_RECOGNITION_API+"/recognize/"
            resp = requests.post(url, files={"image": image})
            result = resp.json()["name"]
            return render(request, "results.html", {"result": result, "back_url": reverse('image')})
        else:
            return render(request, self.template_name)

