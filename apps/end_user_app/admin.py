from django.contrib import admin
from .models import PurchaseRequest, PurchaseRequestItems

# Register your models here.
admin.site.register(PurchaseRequest)
admin.site.register(PurchaseRequestItems)