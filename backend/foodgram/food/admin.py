from django.contrib import admin

from .models import Tags, Ingredients, IngredientInReceipt, Receipts


admin.site.register(
    (Tags, IngredientInReceipt, Ingredients, Receipts)
)
