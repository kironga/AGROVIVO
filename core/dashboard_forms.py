from pathlib import Path
from uuid import uuid4

from django import forms
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import slugify

from catalog.models import CropStage, Product
from orders.models import Order


class ProductAdminForm(forms.ModelForm):
    key_benefits_text = forms.CharField(label="Key benefits", required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One benefit per line"}))
    best_for_text = forms.CharField(label="Recommended for", required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "One crop or use per line"}))
    crops_text = forms.CharField(label="Suitable crops", required=False, widget=forms.TextInput(attrs={"placeholder": "Tomato, Avocado, French Beans"}))
    target_crop_area_text = forms.CharField(label="Target crops / areas", required=False, widget=forms.TextInput(attrs={"placeholder": "Tomato, greenhouse crops, ornamentals"}), help_text="Separate entries with commas.")
    available_packs_text = forms.CharField(label="Available pack sizes", required=False, widget=forms.TextInput(attrs={"placeholder": "100 g, 500 g, 1 kg"}), help_text="Separate pack sizes with commas.")
    static_image = forms.ChoiceField(label="Choose an existing product photo", required=False)
    image_source = forms.CharField(label="Or use an image URL", required=False, widget=forms.TextInput(attrs={"placeholder": "https://example.com/product-photo.jpg"}))
    image_upload = forms.ImageField(label="Or upload an image from this computer", required=False, widget=forms.ClearableFileInput(attrs={"accept": "image/*"}), help_text="JPEG, PNG, WebP or GIF. Maximum 8 MB.")

    class Meta:
        model = Product
        fields = ["name", "slug", "farmer_focus", "primary_role", "product_type", "purpose", "formulation", "active_ingredients", "target_crop_area_text", "available_packs_text", "mode_of_action", "target_problems", "application_rate", "application_method", "application_guide", "pre_harvest_interval", "re_entry_interval", "safety_precautions", "compatibility", "key_benefits_text", "best_for_text", "crops_text", "stage", "price_kes", "stock", "technical_sheet", "featured", "active"]
        labels = {"purpose": "Product description", "farmer_focus": "Short product tagline", "primary_role": "Product category / role", "product_type": "Product type", "formulation": "Formulation", "active_ingredients": "Active ingredients / composition", "mode_of_action": "Mode of action", "target_problems": "Target pests, diseases or deficiencies", "application_rate": "Application rate", "application_method": "Mode of application", "application_guide": "Application guide", "pre_harvest_interval": "Pre-harvest interval (PHI)", "re_entry_interval": "Re-entry interval", "safety_precautions": "Safety precautions", "compatibility": "Compatibility / mixing notes", "price_kes": "Price (KES)", "stock": "Available stock", "technical_sheet": "Technical sheet URL"}
        widgets = {"purpose": forms.Textarea(attrs={"rows": 5}), "active_ingredients": forms.Textarea(attrs={"rows": 3}), "mode_of_action": forms.Textarea(attrs={"rows": 3}), "target_problems": forms.Textarea(attrs={"rows": 3}), "application_rate": forms.Textarea(attrs={"rows": 3}), "application_method": forms.Textarea(attrs={"rows": 3}), "application_guide": forms.Textarea(attrs={"rows": 5}), "safety_precautions": forms.Textarea(attrs={"rows": 3}), "compatibility": forms.Textarea(attrs={"rows": 3}), "pre_harvest_interval": forms.TextInput(attrs={"placeholder": "As stated on approved label"}), "re_entry_interval": forms.TextInput(attrs={"placeholder": "As stated on approved label"}), "slug": forms.TextInput(attrs={"placeholder": "Leave blank to generate from product name"}), "price_kes": forms.NumberInput(attrs={"min": 0}), "stock": forms.NumberInput(attrs={"min": 0})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stage"].choices = [("", "Choose a crop stage"), *CropStage.choices]
        image_dir = settings.BASE_DIR / "static" / "images" / "product-photos"
        image_choices = [("", "No image selected")]
        if image_dir.exists():
            image_choices.extend((f"/static/images/product-photos/{path.name}", path.name) for path in sorted(image_dir.iterdir()) if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"})
        self.fields["static_image"].choices = image_choices
        if self.instance and self.instance.pk:
            self.initial["key_benefits_text"] = "\n".join(self.instance.key_benefits or [])
            self.initial["best_for_text"] = "\n".join(self.instance.best_for or [])
            self.initial["crops_text"] = ", ".join(self.instance.crops or [])
            self.initial["target_crop_area_text"] = ", ".join(self.instance.target_crop_area or [])
            self.initial["available_packs_text"] = ", ".join(self.instance.available_packs or [])
            current_image = (self.instance.images or [""])[0]
            if current_image in dict(image_choices):
                self.initial["static_image"] = current_image
            elif current_image:
                self.initial["image_source"] = current_image

    def clean_image_upload(self):
        image = self.cleaned_data.get("image_upload")
        if image:
            if image.size > 8 * 1024 * 1024:
                raise forms.ValidationError("Image must be 8 MB or smaller.")
            if Path(image.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                raise forms.ValidationError("Upload a JPEG, PNG, WebP or GIF image.")
        return image

    def clean_image_source(self):
        value = self.cleaned_data.get("image_source", "").strip()
        if value and not (value.startswith(("https://", "http://", "/media/", "/static/"))):
            raise forms.ValidationError("Use an https/http image URL or a /static/ or /media/ image path.")
        return value

    def clean_slug(self):
        slug = self.cleaned_data.get("slug") or slugify(self.cleaned_data.get("name", ""))
        if not slug:
            raise forms.ValidationError("Enter a product name so a page address can be generated.")
        qs = Product.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("That product page address is already in use.")
        return slug

    @staticmethod
    def _split_lines(value):
        return [part.strip() for line in value.splitlines() for part in line.split(",") if part.strip()]

    def save(self, commit=True):
        product = super().save(commit=False)
        product.key_benefits = self._split_lines(self.cleaned_data.get("key_benefits_text", ""))
        product.best_for = self._split_lines(self.cleaned_data.get("best_for_text", ""))
        product.crops = self._split_lines(self.cleaned_data.get("crops_text", ""))
        product.target_crop_area = self._split_lines(self.cleaned_data.get("target_crop_area_text", ""))
        product.available_packs = self._split_lines(self.cleaned_data.get("available_packs_text", ""))
        upload = self.cleaned_data.get("image_upload")
        if upload:
            extension = Path(upload.name).suffix.lower()
            filename = default_storage.save(f"product-photos/{uuid4().hex}{extension}", upload)
            image = default_storage.url(filename)
        else:
            image = self.cleaned_data.get("static_image", "") or self.cleaned_data.get("image_source", "").strip()
        product.images = [image] if image else []
        if commit:
            product.save()
            self.save_m2m()
        return product


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "payment_ref"]
        labels = {"payment_ref": "Payment reference"}
        widgets = {"payment_ref": forms.TextInput(attrs={"placeholder": "M-Pesa receipt or payment reference"})}
