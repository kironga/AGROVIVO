import pytest
from django.urls import reverse
from catalog.models import Product
from .models import Order
@pytest.mark.django_db
def test_checkout_creates_cod_order_and_decrements_stock(client):
 p=Product.objects.create(name="FitoMaster",slug="fitomaster",farmer_focus="ROOTS FIRST",primary_role="Root",formulation="NPK",stage="ESTABLISH",price_kes=1200,stock=5)
 session=client.session; session["cart"]={str(p.id):2}; session.save()
 response=client.post(reverse("checkout"),{"name":"Amina Farmer","phone":"+254712345678","county":"Nairobi","town":"Karen","payment_method":"COD"})
 assert response.status_code==302
 assert Order.objects.count()==1
 p.refresh_from_db(); assert p.stock==3
 assert Order.objects.first().total_kes==2750

@pytest.mark.django_db
def test_checkout_normalizes_local_kenyan_mobile_number(client):
 p=Product.objects.create(name="FitoMaster",slug="fitomaster",farmer_focus="ROOTS FIRST",primary_role="Root",formulation="NPK",stage="ESTABLISH",price_kes=1200,stock=5)
 session=client.session; session["cart"]={str(p.id):1}; session.save()
 response=client.post(reverse("checkout"),{"name":"Amina Farmer","phone":"0712345678","county":"Nairobi","town":"Karen","payment_method":"COD"})
 assert response.status_code==302
 assert Order.objects.get().customer_phone=="+254712345678"
