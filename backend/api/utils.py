import os
from io import BytesIO

from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm


def generate_shopping_cart_pdf(user):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    font_path = os.path.join("fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))
    p.setFont("DejaVu", 12)

    all_obj_shopping_cart = user.user_shopping_cart_recipes.all()
    p.drawString(100, height - 100, "Список покупок рецептов")
    y_position = height - 130

    for recipe in all_obj_shopping_cart:
        p.drawString(100, y_position, f"Номер: {recipe.id}")
        y_position -= 20
        p.drawString(100, y_position, f"Название: {recipe.name}")
        y_position -= 20
        p.drawString(100, y_position, f"Описание: {recipe.text}")
        y_position -= 20
        ingredients = ", ".join([
            f"{amount.amount} {amount.ingredient.unit} {amount.ingredient.name}"
            for amount in recipe.recipe_ingredients.select_related('ingredient').all()
        ])
        p.drawString(
            100,
            y_position,
            f"Ингредиенты: {ingredients}"
        )
        y_position -= 20
        p.drawString(
            100,
            y_position,
            f"Время готовки: {recipe.cooking_time} minutes",
        )
        y_position -= 20
        p.drawString(100, y_position, "Изображение: ")
        y_position -= 20
        if recipe.image:
            image_path = recipe.image.path
            p.drawImage(
                image_path,
                100,
                y_position - 100,
                width=200,
                height=100
            )
            y_position -= 120
        else:
            y_position -= 60
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
