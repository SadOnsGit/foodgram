import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """
    Валидация Username пользователя по паттерну
    отправка недопустимых символов пользователю.
    """
    if value.lower() == "me":
        raise ValidationError('Имя пользователя не может быть "me".')
    invalid_chars = re.sub(r"[\w.@+-]", "", value)
    if invalid_chars:
        invalid_chars = "".join(sorted(set(invalid_chars)))
        raise ValidationError(
            f"Имя содержит недопустимые символы: {invalid_chars}. "
            "Разрешены только буквы, цифры и символы @/./+/-/_."
        )
