from typing import Any

# ========== ЗАГОТОВКИ ФУНКЦИЙ ==========
def create_record():
    """Добавляет новую запись в существующую таблицу."""
    pass

def select_record():
    """Возвращает записи, подходящие под запрос или фильтр."""
    pass

def update_record():
    """Обновляет поля существующей записи по идентификатору или фильтру."""
    pass

def delete_record():
    """Удаляет запись из таблицы по идентификатору или фильтру."""
    pass

def create_table():
    pass

def list_tables():
    pass

def get_table():
    pass

def delete_table():
    pass

# ========== ОСНОВНОЙ КОД ==========

# Словарь для хранения всех таблиц
TABLES: dict[str, list] = {}

def init_database():
    """Инициализация базы данных"""
    if "Student" not in TABLES:
        TABLES["Student"] = []
    if "Teachers" not in TABLES:
        TABLES["Teachers"] = []

init_database()

# Для обратной совместимости - Student ссылается на TABLES["Student"]
Student = TABLES["Student"]

# Определяем тип записи студента
type StudentRecord = tuple[int, str, str, int, str]

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ТАБЛИЦАМИ ==========

def create_table(table_name: str) -> bool:
    """
    Создает новую таблицу с указанным именем.
    Возвращает True, если таблица создана, False если таблица уже существует.
    """
    table_name = table_name.strip()

    if not table_name:
        raise ValueError("Имя таблицы не может быть пустым")

    if table_name in TABLES:
        print(f"Таблица '{table_name}' уже существует")
        return False

    # Создаем новую пустую таблицу
    TABLES[table_name] = []
    print(f"Таблица '{table_name}' успешно создана")
    return True


def list_tables() -> list[str]:
    """Возвращает список всех существующих таблиц"""
    return list(TABLES.keys())


def get_table(table_name: str) -> list | None:
    """Возвращает таблицу по имени или None, если таблица не найдена"""
    return TABLES.get(table_name)


def delete_table(table_name: str) -> bool:
    """Удаляет таблицу (осторожно!)"""
    if table_name == "Student":
        print("Таблицу Student нельзя удалить")
        return False

    if table_name in TABLES:
        del TABLES[table_name]
        print(f"Таблица '{table_name}' удалена")
        return True
    return False


# ========== CRUD ОПЕРАЦИИ ==========

def create_record(
    student_id: int,   # Уникальный идентификатор записи
    first_name: str,   # Имя
    second_name: str,  # Фамилия
    age: int,          # Возраст
    sex: str,          # Пол
) -> tuple:
    """
    Создаёт новую запись и добавляет её в таблицу Student.

    Выполняется валидация возраста и проверка уникальности идентификатора.
    В случае нарушения условий возбуждается исключение ValueError.
    """
    # Проверка корректности возраста.
    if age < 0:
        raise ValueError("Поле age не может быть отрицательным.")

    # Проверка уникальности идентификатора.
    if any(record[0] == student_id for record in Student):
        raise ValueError(f"Запись с id={student_id} уже существует.")

    # Формирование новой записи.
    new_record = (
        student_id,
        first_name.strip(),
        second_name.strip(),
        age,
        sex.strip(),
    )

    # Добавление записи в таблицу.
    Student.append(new_record)

    # Возврат созданной записи.
    return new_record


def select_record(
    student_id: int | None = None,   # Фильтр по идентификатору
    first_name: str | None = None,   # Фильтр по имени
    second_name: str | None = None,  # Фильтр по фамилии
    age: int | None = None,          # Фильтр по возрасту
    sex: str | None = None,          # Фильтр по полу
) -> list[StudentRecord]:
    """
    Выполняет выборку записей из таблицы Student
    в соответствии с переданными фильтрами.

    Если фильтры не заданы, возвращается копия всей таблицы.
    """
    # Проверка отсутствия всех фильтров.
    if (
        student_id is None
        and first_name is None
        and second_name is None
        and age is None
        and sex is None
    ):
        return Student.copy()

    # Формирование результирующего списка.
    result: list[StudentRecord] = []

    # Итерация по всем записям таблицы.
    for record in Student:
        # Проверка соответствия каждому фильтру.
        if student_id is not None and record[0] != student_id:
            continue
        if first_name is not None and record[1] != first_name:
            continue
        if second_name is not None and record[2] != second_name:
            continue
        if age is not None and record[3] != age:
            continue
        if sex is not None and record[4] != sex:
            continue

        # Если запись удовлетворяет всем заданным условиям,
        # она добавляется в результирующий список.
        result.append(record)

    # Возврат списка найденных записей.
    return result


def update_record(
        student_id: int,
        first_name: str | None = None,
        second_name: str | None = None,
        age: int | None = None,
        sex: str | None = None
) -> tuple | None:
    """
    Обновляет запись с указанным student_id.
    Возвращает обновленную запись или None, если запись не найдена.
    """
    # Ищем запись по id
    for i, record in enumerate(Student):
        if record[0] == student_id:
            # Создаем новую запись с обновленными полями
            new_record = (
                student_id,
                first_name if first_name is not None else record[1],
                second_name if second_name is not None else record[2],
                age if age is not None else record[3],
                sex if sex is not None else record[4]
            )

            # Валидация возраста
            if new_record[3] < 0:
                raise ValueError("Поле age не может быть отрицательным.")

            # Заменяем запись
            Student[i] = new_record
            return new_record

    # Если запись не найдена
    return None


def delete_record(student_id: int) -> bool:
    """
    Удаляет запись с указанным student_id.
    Возвращает True, если запись была удалена, иначе False.
    """
    for i, record in enumerate(Student):
        if record[0] == student_id:
            del Student[i]
            return True

    return False