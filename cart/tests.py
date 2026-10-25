import pytest
from django.urls import reverse
from catalog.models import Product
@pytest.mark.django_db
def test_add_to_cart_is_session_based(client):
 p=Product.objects.create(name="FitoMaster",slug="fitomaster",farmer_focus="ROOTS FIRST",primary_role="Root",formulation="NPK",stage="ESTABLISH",price_kes=1200,stock=5)
 response=client.post(reverse("cart_add",kwargs={"product_id":p.id}),{"quantity":2})
 assert response.status_code==302
 assert client.session["cart"][str(p.id)]==2
 assert client.get(reverse("cart")).status_code==200
