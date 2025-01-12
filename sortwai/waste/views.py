import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView
from geopy import Nominatim

from sortwai.waste.models import BarCode, Category, Document, Location, Municipality


def get_active_municipality(request):
    if city := request.COOKIES.get("municipality"):
        municipality = Municipality.objects.filter(name=city)
        if municipality.exists():
            return municipality.first()

    return Municipality.objects.first()


class CategoryListView(ListView):
    template_name = "categories.html"

    def get_queryset(self):
        return Category.objects.filter(
            municipality=get_active_municipality(self.request)
        ).select_related("target")

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
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
                response = JsonResponse({"city": city})
                response.set_cookie("municipality", city, max_age=7 * 24 * 60 * 60)
                return response
            else:
                return JsonResponse({"error": "City not found."}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)
