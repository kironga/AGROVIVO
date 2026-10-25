from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from catalog.models import Product
class StaticViewSitemap(Sitemap):
 def items(self): return ["home","about","contact","products","programmes"]
 def location(self,item): return reverse(item)
class ProductSitemap(Sitemap):
 def items(self): return Product.objects.filter(active=True)
