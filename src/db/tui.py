from src.db.backend.memory import (create_record, select_record, update_record, delete_record,
    create_table, list_tables, get_table
)
from src.db.backend.errors import InvalidAgeError, DuplicateIDError, StudentTableError


def _print_menu() -> None:
    # Символ \n обозначает перевод строки.
    print("\n=== База студентов ===")
    print("1. Добавить запись")
    print("2. Показать все записи")
    print("3. Найти записи по фильтру")
    print("4. Обновить запись")
    print("5. Удалить запись")
    print("6. Создать новую таблицу") 
    print("7. Показать все таблицы") 
    print("0. Выход")


def _create_new_table() -> None:
    """Создание новой таблицы"""
    print("\n--- Создание новой таблицы ---")
    print("Существующие таблицы:", ", ".join(list_tables()))

    table_name = input("Введите имя новой таблицы: ").strip()

    try:
        create_table(table_name)
    except ValueError as exc:
        print(f"✗ Ошибка: {exc}")


def _show_tables() -> None:
    """Показать все таблицы"""
    print("\n--- Доступные таблицы ---")
    tables = list_tables()
    for i, table in enumerate(tables, 1):
        count = len(get_table(table))
        print(f"{i}. {table} (записей: {count})")


# Функция чтения целочисленного значения из консоли.
def _read_int(prompt: str) -> int:
    # Используется цикл с повторением до получения корректного ввода.
    while True:
        # Получение строки из консоли с удалением пробельных символов
        # в начале и в конце строки.
        raw = input(prompt).strip()
        try:
            # Преобразование строки к целому числу.
            return int(raw)
        except ValueError:
            # Исключение возникает при невозможности преобразования.
            # Пользователю выводится сообщение об ошибке,
            # после чего ввод повторяется.
            print("Ошибка: введите целое число.")

# Функция добавления новой записи в базу данных.
def _add_student() -> None:
    print("\nДобавление записи")

    student_id = _read_int("id: ")
    first_name = input("first_name: ").strip()
    second_name = input("second_name: ").strip()
    age = _read_int("age: ")
    sex = input("sex: ").strip()

    try:
        # Вызов функции слоя бизнес-логики.
        record = create_record(student_id, first_name, second_name, age, sex)

        # В случае успешного добавления запись выводится в консоль.
        print(f"Запись добавлена: {record}")

    except (ValueError, DuplicateIDError, InvalidAgeError) as exc:
        # Обработка ошибок валидации.
        print(f"Ошибка: {exc}")

# Вспомогательная функция вывода списка записей.
def _print_records(records: list[tuple[int, str, str, int, str]]) -> None:
    # Проверка на пустой список.
    if not records:
        print("Записи не найдены.")
        return

    # Последовательный вывод записей.
    for record in records:
        print(record)

# Функция вывода всех записей из базы данных.
def _show_all_students() -> None:
    print("\nСписок записей")
    _print_records(select_record())

# Функция чтения необязательного целочисленного значения.
# Пустой ввод интерпретируется как отсутствие фильтра (None).
def _read_optional_int(prompt: str) -> int | None:
    while True:
        raw = input(prompt).strip()

        if raw == "":
            return None

        try:
            return int(raw)
        except ValueError:
            print("Ошибка: введите целое число или оставьте поле пустым.")

# Функция поиска записей по заданным фильтрам.
def _find_students_by_filter() -> None:
    print("\nПоиск по фильтру (Enter = пропустить поле)")

    student_id = _read_optional_int("id: ")

    # Оператор or возвращает первое истинное значение.
    # Если строка после strip() пуста, будет возвращено None.
    first_name = input("first_name: ").strip() or None
    second_name = input("second_name: ").strip() or None

    age = _read_optional_int("age: ")
    sex = input("sex: ").strip() or None

    records = select_record(
        student_id=student_id,
        first_name=first_name,
        second_name=second_name,
        age=age,
        sex=sex,
    )

    _print_records(records)

def _update_student() -> None:
    """Обновление данных студента"""
    print("\n--- Обновление записи ---")

    student_id = _read_int("id записи для обновления: ")

    # Проверяем, существует ли запись
    existing = select_record(student_id=student_id)
    if not existing:
        print(f"✗ Запись с id={student_id} не найдена")
        return

    print("Текущие данные:", existing[0])
    print("(Оставьте поле пустым, чтобы не менять)")

    # Чтение новых значений
    first_name = input("new first_name (Enter - без изменений): ")
    first_name = first_name if first_name else None

    second_name = input("new second_name (Enter - без изменений): ")
    second_name = second_name if second_name else None

    age_input = input("new age (Enter - без изменений): ")
    age = int(age_input) if age_input else None

    sex = input("new sex (Enter - без изменений): ")
    sex = sex if sex else None

    try:
        updated = update_record(student_id, first_name, second_name, age, sex)

        if updated:
            print(f"✓ Запись обновлена: {updated}")
        else:
            print("✗ Не удалось обновить запись (запись не найдена)")
    except InvalidAgeError as exc:
        print(f"✗ Ошибка валидации возраста: {exc}")
    except StudentTableError as exc:
        print(f"✗ Ошибка базы данных: {exc}")

def _delete_student() -> None:
    """Удаление студента"""
    print("\n--- Удаление записи ---")

    student_id = _read_int("id записи для удаления: ")

    # Показываем запись перед удалением
    existing = select_record(student_id=student_id)
    if not existing:
        print(f"✗ Запись с id={student_id} не найдена")
        return

    print("Запись для удаления:", existing[0])
    confirm = input("Вы уверены? (д/н): ").strip().lower()

    if confirm == 'д' or confirm == 'yes' or confirm == 'y':
        deleted = delete_record(student_id)
        if deleted:
            print(f"✓ Запись с id={student_id} удалена")
        else:
            print(f"✗ Не удалось удалить запись")
    else:
        print("Удаление отменено")

def run() -> None:
    """
    Запускает основной цикл текстового пользовательского интерфейса.

    Цикл выполняется до тех пор, пока пользователь явно
    не выберет завершение программы.
    """
    while True:
        # Отображение меню доступных действий.
        _print_menu()

        # Получение команды пользователя.
        # Метод strip() удаляет пробельные символы
        # в начале и в конце строки.
        action = input("Выберите действие: ").strip()

        # Диспетчеризация пользовательской команды.
        if action == "1":
            _add_student()

        elif action == "2":
            _show_all_students()

        elif action == "3":
            _find_students_by_filter()

        elif action == "4":
            _update_student()

        elif action == "5":
            _delete_student()

        elif action == '6':  # НОВЫЙ ПУНКТ
            _create_new_table()

        elif action == '7':  # НОВЫЙ ПУНКТ
            _show_tables()

        elif action == "0":
            # Завершение работы программы.
            print("Выход из программы.")
            break

        else:
            # Обработка некорректного ввода команды.
            print("Неизвестная команда. Повторите ввод.")