from django.contrib import admin
from .models import Product,CropProgramme
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
 list_display=("name","stage","price_kes","stock","active","featured")
 list_filter=("stage","active","featured")
 search_fields=("name","primary_role","formulation")
 prepopulated_fields={"slug":("name",)}
@admin.register(CropProgramme)
class CropProgrammeAdmin(admin.ModelAdmin):
 list_display=("crop_name","slug")
 prepopulated_fields={"slug":("crop_name",)}
