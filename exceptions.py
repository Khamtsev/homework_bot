class HomeworkKeyError(Exception):
    """Отсутсвует необходимый ключ в словаре."""

    pass


class TokenError(Exception):
    """Отсутствует необходимый для работы токен."""

    pass


class WrongStatus(Exception):
    """Непредвиденный статус домашней работы."""

    pass
