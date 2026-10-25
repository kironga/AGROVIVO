from django.db import models
class CropStage(models.TextChoices):
 ESTABLISH="ESTABLISH","Establish"
 VEGETATIVE="VEGETATIVE","Vegetative"
 BALANCED_NUTRITION="BALANCED_NUTRITION","Balanced nutrition"
 FLOWERING_SET="FLOWERING_SET","Flowering & set"
 GROWTH_REGULATION="GROWTH_REGULATION","Growth regulation"
 FRUIT_STRENGTH="FRUIT_STRENGTH","Fruit strength"
 STRESS_SUPPORT="STRESS_SUPPORT","Stress support"
 MICRONUTRIENTS="MICRONUTRIENTS","Micronutrients"
 BULKING_FINISH="BULKING_FINISH","Bulking & finish"
class Product(models.Model):
 name=models.CharField(max_length=120)
 slug=models.SlugField(unique=True)
 farmer_focus=models.CharField(max_length=120)
 primary_role=models.CharField(max_length=160)
 purpose=models.TextField(blank=True)
 formulation=models.CharField(max_length=240)
 key_benefits=models.JSONField(default=list)
 best_for=models.JSONField(default=list)
 stage=models.CharField(max_length=32,choices=CropStage.choices)
 crops=models.JSONField(default=list)
 price_kes=models.PositiveIntegerField(help_text="Placeholder price in KES; confirm before launch.")
 stock=models.PositiveIntegerField(default=0)
 images=models.JSONField(default=list,blank=True)
 technical_sheet=models.URLField(blank=True)
 featured=models.BooleanField(default=False)
 active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta: ordering=["name"]
 def __str__(self): return self.name
 def get_absolute_url(self):
  from django.urls import reverse
  return reverse("product_detail",kwargs={"slug":self.slug})
class CropProgramme(models.Model):
 crop_name=models.CharField(max_length=100,unique=True)
 slug=models.SlugField(unique=True)
 hero_image=models.URLField(blank=True)
 stages=models.JSONField(default=list)
 def __str__(self): return self.crop_name
