import random, string

from food.models import Recipe


def generate_unique_short_code(length):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not Recipe.objects.filter(short_code=code).exists():
            return code