import pytest
from django.urls import reverse
from .models import Product
@pytest.mark.django_db
def test_catalog_and_detail_render(client):
 p=Product.objects.create(name="FitoMaster",slug="fitomaster",farmer_focus="ROOTS FIRST",primary_role="Root establishment",formulation="NPK",stage="ESTABLISH",price_kes=1200,stock=10)
 assert client.get(reverse("products")).status_code==200
 response=client.get(reverse("product_detail",kwargs={"slug":p.slug}))
 assert response.status_code==200
 assert b"FitoMaster" in response.content
