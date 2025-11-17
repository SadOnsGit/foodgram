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

    # Подключаем шрифт с поддержкой кириллицы
    font_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans.ttf")
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не найден: {font_path}")

    pdfmetrics.registerFont(TTFont("DejaVu", font_path))
    p.setFont("DejaVu", 14)

    # Заголовок
    p.drawCenteringText(width / 2, height - 40 * mm, "Список покупок")
    p.setFont("DejaVu", 12)
    y = height - 60 * mm

    recipes = user.user_shopping_cart.select_related('recipe').all()

    for recipe in recipes:
        recipe = recipe.recipe  # если у тебя связь через промежуточную модель

        p.drawString(20 * mm, y, f"• {recipe.name}")
        y -= 7 * mm

        p.setFont("DejaVu", 10)
        p.setFillGray(0.4)
        p.drawString(
            25 * mm,
            y,
            f"    Готовка: {recipe.cooking_time} мин",
        )
        y -= 6 * mm
        p.setFillGray(0)
        p.setFont("DejaVu", 12)

        if y < 50 * mm:  # переходим на новую страницу, если места мало
            p.showPage()
            p.setFont("DejaVu", 12)
            y = height - 40 * mm

        y -= 10 * mm  # отступ между рецептами

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer