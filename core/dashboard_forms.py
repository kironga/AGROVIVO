from django import forms
from django.utils.text import slugify

from catalog.models import CropStage, Product
from orders.models import Order


class ProductAdminForm(forms.ModelForm):
    key_benefits_text = forms.CharField(label="Key benefits", required=False, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One benefit per line"}))
    best_for_text = forms.CharField(label="Recommended for", required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "One crop or use per line"}))
    crops_text = forms.CharField(label="Suitable crops", required=False, widget=forms.TextInput(attrs={"placeholder": "Tomato, Avocado, French Beans"}))
    image_source = forms.CharField(label="Product image path or URL", required=False, help_text="Use an uploaded static image path such as /static/images/product-photos/photo.jpg, or a public image URL.")

    class Meta:
        model = Product
        fields = ["name", "slug", "farmer_focus", "primary_role", "purpose", "formulation", "stage", "price_kes", "stock", "technical_sheet", "featured", "active"]
        labels = {"purpose": "Product description", "farmer_focus": "Short product tagline", "primary_role": "Product category / role", "formulation": "Composition / formulation", "price_kes": "Price (KES)", "stock": "Available stock", "technical_sheet": "Technical sheet URL"}
        widgets = {"purpose": forms.Textarea(attrs={"rows": 5}), "slug": forms.TextInput(attrs={"placeholder": "Leave blank to generate from product name"}), "price_kes": forms.NumberInput(attrs={"min": 0}), "stock": forms.NumberInput(attrs={"min": 0})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stage"].choices = [("", "Choose a crop stage"), *CropStage.choices]
        if self.instance and self.instance.pk:
            self.initial["key_benefits_text"] = "\n".join(self.instance.key_benefits or [])
            self.initial["best_for_text"] = "\n".join(self.instance.best_for or [])
            self.initial["crops_text"] = ", ".join(self.instance.crops or [])
            self.initial["image_source"] = (self.instance.images or [""])[0]

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
        image = self.cleaned_data.get("image_source", "").strip()
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
