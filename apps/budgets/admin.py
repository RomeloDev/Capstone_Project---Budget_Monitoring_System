from django.contrib import admin
from .models import ApprovedBudget, SupportingDocument

# Register your models here.
admin.site.register(ApprovedBudget)
admin.site.register(SupportingDocument)