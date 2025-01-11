# Register your models here.
from django.contrib import admin

from sortwai.waste.models import (
    BarCode,
    Category,
    Document,
    Location,
    Municipality,
    Target,
)


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name"]
    search_fields = ["name", "short_name"]


@admin.register(Target)
class TargeAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "municipality"]
    list_filter = ["color"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "gps_lat", "gps_lon", "municipality"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "municipality"]


@admin.register(BarCode)
class BarCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "product_name", "material_number", "material_type"]
    search_fields = ["product_name", "material_number", "material_type"]
    list_filter = ["material_number", "material_type"]
