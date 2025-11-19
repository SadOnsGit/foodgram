import json
from pathlib import Path
from django.core.management.base import BaseCommand

from food.models import Ingredients


class Command(BaseCommand):
    help = "Загрузка ингредиентов из data/ingredients.json"

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        file_path = base_dir / "data" / "ingredients.json"

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        created = 0
        for item in data:
            obj, is_created = Ingredients.objects.get_or_create(
                name=item["name"].lower().strip(),
                measurement_unit=item["measurement_unit"].strip(),
            )
            if is_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно загружено {created} новых ингредиентов"
            )
        )