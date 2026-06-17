"""Исключения для работы с БД"""

class DatabaseError(Exception):
    """Базовое исключение для всех ошибок БД"""
    pass


class InvalidAgeError(DatabaseError):
    """Ошибка, возникающая при попытке создать запись с некорректным возрастом"""
    pass


class DuplicateIDError(DatabaseError):
    """Ошибка, возникающая при попытке создать запись с уже существующим идентификатором"""
    pass


class RecordNotFoundError(DatabaseError):
    """Ошибка, возникающая когда запись не найдена"""
    pass


class FileDatabaseError(DatabaseError):
    """Ошибка, связанная с работой с файлами БД"""
    pass